"""
Quiz Generation Service Lambda Function

Handles quiz generation, session management, scoring, and adaptive question selection
for the ProCert Learning Platform.
"""

import json
import boto3
import os
import uuid
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import logging
from decimal import Decimal
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')

# Environment variables
QUIZ_SESSIONS_TABLE = os.environ.get('QUIZ_SESSIONS_TABLE')
USER_PROGRESS_TABLE = os.environ.get('USER_PROGRESS_TABLE')
CONTENT_METADATA_TABLE = os.environ.get('CONTENT_METADATA_TABLE')
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX')
AWS_REGION = os.environ.get('AWS_REGION')

# Initialize DynamoDB tables
quiz_sessions_table = dynamodb.Table(QUIZ_SESSIONS_TABLE) if QUIZ_SESSIONS_TABLE else None
user_progress_table = dynamodb.Table(USER_PROGRESS_TABLE) if USER_PROGRESS_TABLE else None
content_metadata_table = dynamodb.Table(CONTENT_METADATA_TABLE) if CONTENT_METADATA_TABLE else None

# Set up OpenSearch client
if OPENSEARCH_ENDPOINT:
    host = OPENSEARCH_ENDPOINT.replace("https://", "")
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
    opensearch_client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_timeout=30
    )
else:
    opensearch_client = None


def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def convert_decimals_to_numbers(obj):
    """Convert Decimal values back to numbers for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_decimals_to_numbers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_numbers(v) for v in obj]
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def get_user_performance_data(user_id: str, certification_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get user's performance data for adaptive question selection.
    
    Args:
        user_id: User identifier
        certification_type: Optional certification filter
        
    Returns:
        Dictionary with performance metrics by category/topic
    """
    try:
        # Query user progress data
        if certification_type:
            response = user_progress_table.query(
                IndexName='UserCertificationIndex',
                KeyConditionExpression='user_id = :user_id AND certification_type = :cert_type',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':cert_type': certification_type
                }
            )
        else:
            response = user_progress_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
        
        progress_items = response.get('Items', [])
        
        # Aggregate performance by category
        category_performance = {}
        for item in progress_items:
            if item.get('progress_type') == 'answered' and item.get('score') is not None:
                category = item.get('category', 'general')
                if category not in category_performance:
                    category_performance[category] = {
                        'total_questions': 0,
                        'correct_answers': 0,
                        'total_score': Decimal('0'),
                        'recent_scores': []
                    }
                
                category_performance[category]['total_questions'] += 1
                score = float(item['score'])
                category_performance[category]['total_score'] += Decimal(str(score))
                category_performance[category]['recent_scores'].append(score)
                
                if score >= 70:  # Consider 70% as correct
                    category_performance[category]['correct_answers'] += 1
        
        # Calculate averages and identify weak areas
        performance_summary = {}
        for category, data in category_performance.items():
            if data['total_questions'] > 0:
                avg_score = float(data['total_score']) / data['total_questions']
                accuracy = data['correct_answers'] / data['total_questions']
                
                performance_summary[category] = {
                    'average_score': avg_score,
                    'accuracy': accuracy,
                    'total_questions': data['total_questions'],
                    'is_weak_area': avg_score < 70 or accuracy < 0.7
                }
        
        return performance_summary
        
    except Exception as e:
        logger.error(f"Error getting user performance data: {str(e)}")
        return {}


def get_recently_answered_questions(user_id: str, days: int = 7) -> List[str]:
    """
    Get list of recently answered question IDs to avoid repetition.
    
    Args:
        user_id: User identifier
        days: Number of days to look back
        
    Returns:
        List of question IDs answered recently
    """
    try:
        # Calculate cutoff timestamp
        cutoff_time = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
        cutoff_iso = datetime.fromtimestamp(cutoff_time, timezone.utc).isoformat()
        
        # Query recent progress
        response = user_progress_table.query(
            KeyConditionExpression='user_id = :user_id',
            FilterExpression='#ts > :cutoff AND progress_type = :answered',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':cutoff': cutoff_iso,
                ':answered': 'answered'
            }
        )
        
        recent_questions = []
        for item in response.get('Items', []):
            content_id = item.get('content_id')
            if content_id:
                recent_questions.append(content_id)
        
        return recent_questions
        
    except Exception as e:
        logger.error(f"Error getting recently answered questions: {str(e)}")
        return []


def search_questions_by_certification(certification_type: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Search for questions in OpenSearch by certification type.
    
    Args:
        certification_type: Certification type to filter by
        limit: Maximum number of questions to retrieve
        
    Returns:
        List of question documents
    """
    try:
        if not opensearch_client:
            logger.error("OpenSearch client not initialized")
            return []
        
        query = {
            "size": limit,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"content_type": "question"}},
                        {"term": {"certification_type": certification_type}}
                    ]
                }
            },
            "_source": [
                "content_id", "text", "certification_type", "category", 
                "difficulty", "metadata"
            ]
        }
        
        response = opensearch_client.search(body=query, index=OPENSEARCH_INDEX)
        
        questions = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Try to parse question data from text or metadata
            question_data = parse_question_from_text(source.get("text", ""))
            if question_data:
                question_data.update({
                    "content_id": source.get("content_id"),
                    "certification_type": source.get("certification_type"),
                    "category": source.get("category", "general"),
                    "difficulty": source.get("difficulty", "intermediate")
                })
                questions.append(question_data)
        
        return questions
        
    except Exception as e:
        logger.error(f"Error searching questions: {str(e)}")
        return []


def parse_question_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse question data from text content.
    This is a simplified parser - in production, you'd want more robust parsing.
    
    Args:
        text: Raw text containing question data
        
    Returns:
        Parsed question data or None
    """
    try:
        # Look for question patterns
        lines = text.strip().split('\n')
        question_text = ""
        options = []
        correct_answer = ""
        explanation = ""
        
        current_section = "question"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if line.lower().startswith("question:") or line.endswith("?"):
                current_section = "question"
                question_text = line.replace("Question:", "").strip()
            elif line.lower().startswith("a)") or line.lower().startswith("a."):
                current_section = "options"
                options.append(line[2:].strip())
            elif line.lower().startswith(("b)", "b.", "c)", "c.", "d)", "d.")):
                if current_section == "options":
                    options.append(line[2:].strip())
            elif line.lower().startswith("answer:") or line.lower().startswith("correct:"):
                current_section = "answer"
                correct_answer = line.split(":", 1)[1].strip()
            elif line.lower().startswith("explanation:"):
                current_section = "explanation"
                explanation = line.split(":", 1)[1].strip()
            elif current_section == "question" and not question_text:
                question_text = line
            elif current_section == "explanation":
                explanation += " " + line
        
        # Validate we have minimum required data
        if question_text and len(options) >= 2:
            # If no explicit correct answer, assume first option
            if not correct_answer and options:
                correct_answer = options[0]
            
            return {
                "question_text": question_text,
                "answer_options": options,
                "correct_answer": correct_answer,
                "explanation": explanation or "No explanation provided."
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing question from text: {str(e)}")
        return None


def select_adaptive_questions(questions: List[Dict[str, Any]], user_performance: Dict[str, Any], 
                            recently_answered: List[str], count: int, 
                            difficulty_preference: str = "mixed") -> List[Dict[str, Any]]:
    """
    Select questions adaptively based on user performance and preferences.
    
    Args:
        questions: Available questions
        user_performance: User's performance data by category
        recently_answered: Recently answered question IDs
        count: Number of questions to select
        difficulty_preference: Difficulty preference (easy, medium, hard, mixed)
        
    Returns:
        Selected questions for the quiz
    """
    try:
        # Filter out recently answered questions
        available_questions = [
            q for q in questions 
            if q.get("content_id") not in recently_answered
        ]
        
        if len(available_questions) < count:
            logger.warning(f"Not enough unique questions available. Requested: {count}, Available: {len(available_questions)}")
            # If we don't have enough unique questions, include some recent ones
            available_questions = questions
        
        # Categorize questions by difficulty and category
        categorized_questions = {
            'weak_areas': [],
            'strong_areas': [],
            'untested_areas': []
        }
        
        for question in available_questions:
            category = question.get('category', 'general')
            
            if category in user_performance:
                perf = user_performance[category]
                if perf['is_weak_area']:
                    categorized_questions['weak_areas'].append(question)
                else:
                    categorized_questions['strong_areas'].append(question)
            else:
                categorized_questions['untested_areas'].append(question)
        
        # Adaptive selection strategy
        selected_questions = []
        
        # 60% from weak areas (if available)
        weak_count = min(int(count * 0.6), len(categorized_questions['weak_areas']))
        selected_questions.extend(random.sample(categorized_questions['weak_areas'], weak_count))
        
        # 25% from untested areas
        remaining_count = count - len(selected_questions)
        untested_count = min(int(count * 0.25), len(categorized_questions['untested_areas']), remaining_count)
        if untested_count > 0:
            selected_questions.extend(random.sample(categorized_questions['untested_areas'], untested_count))
        
        # Fill remaining with strong areas or any available questions
        remaining_count = count - len(selected_questions)
        if remaining_count > 0:
            remaining_questions = categorized_questions['strong_areas']
            if len(remaining_questions) < remaining_count:
                # Add back other questions if needed
                all_remaining = [q for q in available_questions if q not in selected_questions]
                remaining_questions = all_remaining
            
            if remaining_questions:
                additional_count = min(remaining_count, len(remaining_questions))
                selected_questions.extend(random.sample(remaining_questions, additional_count))
        
        # Shuffle the final selection
        random.shuffle(selected_questions)
        
        return selected_questions[:count]
        
    except Exception as e:
        logger.error(f"Error in adaptive question selection: {str(e)}")
        # Fallback to random selection
        return random.sample(questions, min(count, len(questions)))


def create_quiz_session(user_id: str, certification_type: str, question_count: int, 
                       difficulty: str = "mixed") -> Dict[str, Any]:
    """
    Create a new quiz session with adaptively selected questions.
    
    Args:
        user_id: User identifier
        certification_type: Certification type for the quiz
        question_count: Number of questions in the quiz
        difficulty: Difficulty preference
        
    Returns:
        Quiz session data
    """
    try:
        # Generate unique quiz ID
        quiz_id = str(uuid.uuid4())
        
        # Get user performance data
        user_performance = get_user_performance_data(user_id, certification_type)
        
        # Get recently answered questions
        recently_answered = get_recently_answered_questions(user_id)
        
        # Search for available questions
        available_questions = search_questions_by_certification(certification_type, limit=200)
        
        if not available_questions:
            raise ValueError(f"No questions found for certification type: {certification_type}")
        
        # Select questions adaptively
        selected_questions = select_adaptive_questions(
            available_questions, user_performance, recently_answered, 
            question_count, difficulty
        )
        
        if len(selected_questions) < question_count:
            logger.warning(f"Could only find {len(selected_questions)} questions out of {question_count} requested")
        
        # Prepare questions for storage (without correct answers)
        quiz_questions = []
        for i, question in enumerate(selected_questions):
            quiz_question = {
                "question_id": question.get("content_id", f"q_{i}"),
                "question_text": question["question_text"],
                "options": question["answer_options"],
                "correct_answer": question["correct_answer"],  # Store for scoring
                "explanation": question.get("explanation", ""),
                "category": question.get("category", "general"),
                "difficulty": question.get("difficulty", "intermediate")
            }
            quiz_questions.append(quiz_question)
        
        # Create quiz session
        now = datetime.now(timezone.utc)
        quiz_session = {
            "quiz_id": quiz_id,
            "user_id": user_id,
            "certification_type": certification_type,
            "questions": quiz_questions,
            "status": "in_progress",
            "score": None,
            "started_at": now.isoformat(),
            "completed_at": None,
            "time_limit_minutes": Decimal(str(question_count * 2)),  # 2 minutes per question
            "metadata": {
                "difficulty_preference": difficulty,
                "adaptive_selection": True,
                "user_performance_considered": len(user_performance) > 0
            }
        }
        
        # Store in DynamoDB
        quiz_sessions_table.put_item(Item=convert_floats_to_decimal(quiz_session))
        
        # Return quiz without correct answers for the client
        client_quiz = quiz_session.copy()
        for question in client_quiz["questions"]:
            question.pop("correct_answer", None)  # Remove correct answers from client response
        
        return client_quiz
        
    except Exception as e:
        logger.error(f"Error creating quiz session: {str(e)}")
        raise


def submit_quiz_answers(quiz_id: str, user_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Submit quiz answers and calculate score with immediate feedback.
    
    Args:
        quiz_id: Quiz session identifier
        user_answers: List of user answers with question_id and selected_answer
        
    Returns:
        Quiz results with score and feedback
    """
    try:
        # Get quiz session
        response = quiz_sessions_table.get_item(Key={"quiz_id": quiz_id})
        if "Item" not in response:
            raise ValueError("Quiz session not found")
        
        quiz_session = response["Item"]
        
        if quiz_session["status"] != "in_progress":
            raise ValueError("Quiz is not in progress")
        
        # Create answer lookup
        user_answer_lookup = {
            answer["question_id"]: answer["selected_answer"] 
            for answer in user_answers
        }
        
        # Calculate score and prepare feedback
        total_questions = len(quiz_session["questions"])
        correct_answers = 0
        results = []
        
        for question in quiz_session["questions"]:
            question_id = question["question_id"]
            correct_answer = question["correct_answer"]
            user_answer = user_answer_lookup.get(question_id, "")
            
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            if is_correct:
                correct_answers += 1
            
            result = {
                "question_id": question_id,
                "question_text": question["question_text"],
                "options": question["options"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
                "category": question.get("category", "general")
            }
            results.append(result)
        
        # Calculate final score
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Update quiz session
        now = datetime.now(timezone.utc)
        quiz_sessions_table.update_item(
            Key={"quiz_id": quiz_id},
            UpdateExpression="SET #status = :status, score = :score, completed_at = :completed_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "completed",
                ":score": Decimal(str(score)),
                ":completed_at": now.isoformat()
            }
        )
        
        # Record user progress for each question
        user_id = quiz_session["user_id"]
        certification_type = quiz_session["certification_type"]
        
        for result in results:
            try:
                progress_item = {
                    "user_id": user_id,
                    "content_id_certification": f"{result['question_id']}#{certification_type}",
                    "content_id": result["question_id"],
                    "certification_type": certification_type,
                    "progress_type": "answered",
                    "score": Decimal(str(100 if result["is_correct"] else 0)),
                    "time_spent": Decimal("0"),  # Could be calculated from timestamps
                    "timestamp": now.isoformat(),
                    "session_id": quiz_id,
                    "category": result.get("category", "general"),
                    "metadata": {
                        "quiz_id": quiz_id,
                        "user_answer": result["user_answer"],
                        "correct_answer": result["correct_answer"]
                    }
                }
                
                user_progress_table.put_item(Item=convert_floats_to_decimal(progress_item))
                
            except Exception as e:
                logger.error(f"Error recording progress for question {result['question_id']}: {str(e)}")
        
        # Prepare response
        quiz_results = {
            "quiz_id": quiz_id,
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "percentage": score,
            "results": results,
            "completed_at": now.isoformat(),
            "performance_summary": {
                "passed": score >= 70,
                "grade": get_grade_from_score(score),
                "time_taken": "Not tracked"  # Could be calculated
            }
        }
        
        return quiz_results
        
    except Exception as e:
        logger.error(f"Error submitting quiz answers: {str(e)}")
        raise


def get_grade_from_score(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def get_quiz_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get user's quiz history.
    
    Args:
        user_id: User identifier
        limit: Maximum number of quizzes to return
        
    Returns:
        List of quiz sessions
    """
    try:
        response = quiz_sessions_table.query(
            IndexName='UserQuizIndex',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        
        quizzes = response.get('Items', [])
        
        # Remove sensitive data and convert decimals
        for quiz in quizzes:
            # Remove correct answers from questions
            if 'questions' in quiz:
                for question in quiz['questions']:
                    question.pop('correct_answer', None)
        
        return quizzes
        
    except Exception as e:
        logger.error(f"Error getting quiz history: {str(e)}")
        return []


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for quiz generation service.
    
    Supports the following operations:
    - POST /quiz/generate - Generate new quiz
    - POST /quiz/submit - Submit quiz answers
    - GET /quiz/history/{user_id} - Get quiz history
    - GET /quiz/{quiz_id} - Get quiz details
    """
    try:
        # Parse the request
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        body = event.get('body', '{}')
        
        # Parse JSON body
        try:
            request_body = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return create_response(400, {'error': 'Invalid JSON in request body'})
        
        logger.info(f"Processing {http_method} {path}")
        
        # Route the request
        if path.startswith('/quiz/generate') and http_method == 'POST':
            return handle_generate_quiz(request_body)
        elif path.startswith('/quiz/submit') and http_method == 'POST':
            return handle_submit_quiz(request_body)
        elif path.startswith('/quiz/history/') and http_method == 'GET':
            user_id = path_parameters.get('user_id')
            return handle_get_quiz_history(user_id, request_body)
        elif path.startswith('/quiz/') and http_method == 'GET':
            quiz_id = path_parameters.get('quiz_id')
            return handle_get_quiz(quiz_id)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def handle_generate_quiz(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle quiz generation request."""
    try:
        # Validate required fields
        required_fields = ['user_id', 'certification_type']
        for field in required_fields:
            if not request_body.get(field):
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        user_id = request_body['user_id']
        certification_type = request_body['certification_type'].upper()
        question_count = request_body.get('question_count', 10)
        difficulty = request_body.get('difficulty', 'mixed')
        
        # Validate question count
        if not isinstance(question_count, int) or question_count < 1 or question_count > 50:
            return create_response(400, {'error': 'Question count must be between 1 and 50'})
        
        # Generate quiz
        quiz_session = create_quiz_session(user_id, certification_type, question_count, difficulty)
        
        return create_response(200, {
            'message': 'Quiz generated successfully',
            'quiz': quiz_session
        })
        
    except ValueError as e:
        return create_response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        return create_response(500, {'error': 'Failed to generate quiz'})


def handle_submit_quiz(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle quiz submission request."""
    try:
        # Validate required fields
        required_fields = ['quiz_id', 'answers']
        for field in required_fields:
            if not request_body.get(field):
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        quiz_id = request_body['quiz_id']
        answers = request_body['answers']
        
        if not isinstance(answers, list):
            return create_response(400, {'error': 'Answers must be a list'})
        
        # Submit quiz
        results = submit_quiz_answers(quiz_id, answers)
        
        return create_response(200, {
            'message': 'Quiz submitted successfully',
            'results': results
        })
        
    except ValueError as e:
        return create_response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Error submitting quiz: {str(e)}")
        return create_response(500, {'error': 'Failed to submit quiz'})


def handle_get_quiz_history(user_id: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get quiz history request."""
    try:
        if not user_id:
            return create_response(400, {'error': 'User ID is required'})
        
        limit = request_body.get('limit', 20)
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            limit = 20
        
        history = get_quiz_history(user_id, limit)
        
        return create_response(200, {
            'quiz_history': history,
            'total_count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting quiz history: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve quiz history'})


def handle_get_quiz(quiz_id: str) -> Dict[str, Any]:
    """Handle get quiz details request."""
    try:
        if not quiz_id:
            return create_response(400, {'error': 'Quiz ID is required'})
        
        response = quiz_sessions_table.get_item(Key={'quiz_id': quiz_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Quiz not found'})
        
        quiz = response['Item']
        
        # Remove correct answers if quiz is still in progress
        if quiz.get('status') == 'in_progress':
            for question in quiz.get('questions', []):
                question.pop('correct_answer', None)
        
        return create_response(200, {'quiz': quiz})
        
    except Exception as e:
        logger.error(f"Error getting quiz: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve quiz'})


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized API response."""
    # Convert Decimal objects to JSON-serializable numbers
    serializable_body = convert_decimals_to_numbers(body)
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(serializable_body)
    }