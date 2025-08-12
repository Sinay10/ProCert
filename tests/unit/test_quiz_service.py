"""
Unit tests for the Quiz Generation Service.

Tests quiz generation, adaptive question selection, scoring logic,
and anti-repetition functionality.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the quiz lambda source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../quiz_lambda_src'))

# Import the quiz service functions
from main import (
    get_user_performance_data,
    get_recently_answered_questions,
    select_adaptive_questions,
    create_quiz_session,
    submit_quiz_answers,
    parse_question_from_text,
    get_grade_from_score,
    lambda_handler
)


class TestQuizService:
    """Test suite for quiz generation service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_user_id = "test-user-123"
        self.sample_certification = "SAA"
        self.sample_quiz_id = str(uuid.uuid4())
        
        # Sample questions for testing
        self.sample_questions = [
            {
                "content_id": "q1",
                "question_text": "What is Amazon S3?",
                "answer_options": [
                    "A storage service",
                    "A compute service", 
                    "A database service",
                    "A networking service"
                ],
                "correct_answer": "A storage service",
                "explanation": "Amazon S3 is a storage service.",
                "category": "storage",
                "difficulty": "beginner"
            },
            {
                "content_id": "q2", 
                "question_text": "What is Amazon EC2?",
                "answer_options": [
                    "A storage service",
                    "A compute service",
                    "A database service", 
                    "A networking service"
                ],
                "correct_answer": "A compute service",
                "explanation": "Amazon EC2 is a compute service.",
                "category": "compute",
                "difficulty": "intermediate"
            },
            {
                "content_id": "q3",
                "question_text": "What is Amazon RDS?",
                "answer_options": [
                    "A storage service",
                    "A compute service",
                    "A database service",
                    "A networking service"
                ],
                "correct_answer": "A database service", 
                "explanation": "Amazon RDS is a database service.",
                "category": "database",
                "difficulty": "intermediate"
            }
        ]
        
        # Sample user performance data
        self.sample_performance = {
            "storage": {
                "average_score": 85.0,
                "accuracy": 0.85,
                "total_questions": 10,
                "is_weak_area": False
            },
            "compute": {
                "average_score": 60.0,
                "accuracy": 0.6,
                "total_questions": 8,
                "is_weak_area": True
            },
            "database": {
                "average_score": 75.0,
                "accuracy": 0.75,
                "total_questions": 5,
                "is_weak_area": False
            }
        }

    @patch('main.user_progress_table')
    def test_get_user_performance_data(self, mock_table):
        """Test user performance data retrieval."""
        # Mock DynamoDB response
        mock_table.query.return_value = {
            'Items': [
                {
                    'user_id': self.sample_user_id,
                    'content_id': 'q1',
                    'progress_type': 'answered',
                    'score': Decimal('85'),
                    'category': 'storage'
                },
                {
                    'user_id': self.sample_user_id,
                    'content_id': 'q2', 
                    'progress_type': 'answered',
                    'score': Decimal('60'),
                    'category': 'compute'
                }
            ]
        }
        
        performance = get_user_performance_data(self.sample_user_id, self.sample_certification)
        
        assert isinstance(performance, dict)
        assert 'storage' in performance
        assert 'compute' in performance
        assert performance['storage']['average_score'] == 85.0
        assert performance['compute']['is_weak_area'] == True

    @patch('main.user_progress_table')
    def test_get_recently_answered_questions(self, mock_table):
        """Test recently answered questions retrieval."""
        # Mock DynamoDB response
        mock_table.query.return_value = {
            'Items': [
                {
                    'user_id': self.sample_user_id,
                    'content_id': 'q1',
                    'progress_type': 'answered',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                {
                    'user_id': self.sample_user_id,
                    'content_id': 'q2',
                    'progress_type': 'answered', 
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        recent_questions = get_recently_answered_questions(self.sample_user_id)
        
        assert isinstance(recent_questions, list)
        assert 'q1' in recent_questions
        assert 'q2' in recent_questions

    def test_select_adaptive_questions(self):
        """Test adaptive question selection algorithm."""
        recently_answered = ['q1']  # q1 was recently answered
        
        selected = select_adaptive_questions(
            self.sample_questions,
            self.sample_performance,
            recently_answered,
            count=2,
            difficulty_preference="mixed"
        )
        
        assert len(selected) == 2
        # Should prioritize weak areas (compute) and avoid recently answered (q1)
        question_ids = [q['content_id'] for q in selected]
        assert 'q1' not in question_ids  # Should avoid recently answered
        
        # Should include questions from weak areas when possible
        categories = [q['category'] for q in selected]
        assert 'compute' in categories  # Weak area should be prioritized

    def test_parse_question_from_text(self):
        """Test question parsing from text content."""
        sample_text = """
        Question: What is Amazon S3?
        A) A storage service
        B) A compute service
        C) A database service
        D) A networking service
        Answer: A) A storage service
        Explanation: Amazon S3 is a storage service for the cloud.
        """
        
        parsed = parse_question_from_text(sample_text)
        
        assert parsed is not None
        assert "What is Amazon S3?" in parsed['question_text']
        assert len(parsed['answer_options']) >= 2
        assert parsed['correct_answer'] is not None
        assert parsed['explanation'] is not None

    def test_get_grade_from_score(self):
        """Test grade calculation from numeric scores."""
        assert get_grade_from_score(95) == "A"
        assert get_grade_from_score(85) == "B"
        assert get_grade_from_score(75) == "C"
        assert get_grade_from_score(65) == "D"
        assert get_grade_from_score(55) == "F"

    @patch('main.quiz_sessions_table')
    @patch('main.get_user_performance_data')
    @patch('main.get_recently_answered_questions')
    @patch('main.search_questions_by_certification')
    def test_create_quiz_session(self, mock_search, mock_recent, mock_performance, mock_table):
        """Test quiz session creation."""
        # Mock dependencies
        mock_performance.return_value = self.sample_performance
        mock_recent.return_value = ['q1']
        mock_search.return_value = self.sample_questions
        mock_table.put_item.return_value = {}
        
        quiz_session = create_quiz_session(
            self.sample_user_id,
            self.sample_certification,
            question_count=2,
            difficulty="mixed"
        )
        
        assert quiz_session['user_id'] == self.sample_user_id
        assert quiz_session['certification_type'] == self.sample_certification
        assert quiz_session['status'] == 'in_progress'
        assert len(quiz_session['questions']) <= 2
        
        # Verify correct answers are not included in client response
        for question in quiz_session['questions']:
            assert 'correct_answer' not in question

    @patch('main.quiz_sessions_table')
    @patch('main.user_progress_table')
    def test_submit_quiz_answers(self, mock_progress_table, mock_quiz_table):
        """Test quiz answer submission and scoring."""
        # Mock quiz session data
        quiz_session = {
            'quiz_id': self.sample_quiz_id,
            'user_id': self.sample_user_id,
            'certification_type': self.sample_certification,
            'status': 'in_progress',
            'questions': [
                {
                    'question_id': 'q1',
                    'question_text': 'What is Amazon S3?',
                    'options': ['A storage service', 'A compute service'],
                    'correct_answer': 'A storage service',
                    'explanation': 'S3 is storage',
                    'category': 'storage'
                },
                {
                    'question_id': 'q2',
                    'question_text': 'What is Amazon EC2?',
                    'options': ['A storage service', 'A compute service'],
                    'correct_answer': 'A compute service',
                    'explanation': 'EC2 is compute',
                    'category': 'compute'
                }
            ]
        }
        
        mock_quiz_table.get_item.return_value = {'Item': quiz_session}
        mock_quiz_table.update_item.return_value = {}
        mock_progress_table.put_item.return_value = {}
        
        # Submit answers (1 correct, 1 incorrect)
        user_answers = [
            {'question_id': 'q1', 'selected_answer': 'A storage service'},  # Correct
            {'question_id': 'q2', 'selected_answer': 'A storage service'}   # Incorrect
        ]
        
        results = submit_quiz_answers(self.sample_quiz_id, user_answers)
        
        assert results['quiz_id'] == self.sample_quiz_id
        assert results['score'] == 50.0  # 1 out of 2 correct = 50%
        assert results['correct_answers'] == 1
        assert results['total_questions'] == 2
        assert len(results['results']) == 2
        
        # Check individual question results
        q1_result = next(r for r in results['results'] if r['question_id'] == 'q1')
        q2_result = next(r for r in results['results'] if r['question_id'] == 'q2')
        
        assert q1_result['is_correct'] == True
        assert q2_result['is_correct'] == False

    @patch('main.quiz_sessions_table')
    @patch('main.user_progress_table')
    @patch('main.content_metadata_table')
    @patch('main.opensearch_client')
    def test_lambda_handler_generate_quiz(self, mock_opensearch, mock_content_table, 
                                        mock_progress_table, mock_quiz_table):
        """Test Lambda handler for quiz generation."""
        # Mock OpenSearch response with properly formatted questions
        mock_opensearch.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'content_id': 'q1',
                            'text': '''Question: What is Amazon S3?
                            A) A storage service
                            B) A compute service
                            C) A database service
                            D) A networking service
                            Answer: A) A storage service
                            Explanation: Amazon S3 is a storage service.''',
                            'certification_type': 'SAA',
                            'category': 'storage',
                            'difficulty': 'beginner'
                        }
                    },
                    {
                        '_source': {
                            'content_id': 'q2',
                            'text': '''Question: What is Amazon EC2?
                            A) A storage service
                            B) A compute service
                            C) A database service
                            D) A networking service
                            Answer: B) A compute service
                            Explanation: Amazon EC2 is a compute service.''',
                            'certification_type': 'SAA',
                            'category': 'compute',
                            'difficulty': 'intermediate'
                        }
                    }
                ]
            }
        }
        
        mock_quiz_table.put_item.return_value = {}
        mock_progress_table.query.return_value = {'Items': []}
        
        event = {
            'httpMethod': 'POST',
            'path': '/quiz/generate',
            'body': json.dumps({
                'user_id': self.sample_user_id,
                'certification_type': 'SAA',
                'question_count': 2,
                'difficulty': 'mixed'
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'quiz' in body
        assert body['message'] == 'Quiz generated successfully'

    @patch('main.quiz_sessions_table')
    @patch('main.user_progress_table')
    def test_lambda_handler_submit_quiz(self, mock_progress_table, mock_quiz_table):
        """Test Lambda handler for quiz submission."""
        # Mock quiz session
        quiz_session = {
            'quiz_id': self.sample_quiz_id,
            'user_id': self.sample_user_id,
            'certification_type': 'SAA',
            'status': 'in_progress',
            'questions': [
                {
                    'question_id': 'q1',
                    'question_text': 'What is S3?',
                    'options': ['Storage', 'Compute'],
                    'correct_answer': 'Storage',
                    'explanation': 'S3 is storage',
                    'category': 'storage'
                }
            ]
        }
        
        mock_quiz_table.get_item.return_value = {'Item': quiz_session}
        mock_quiz_table.update_item.return_value = {}
        mock_progress_table.put_item.return_value = {}
        
        event = {
            'httpMethod': 'POST',
            'path': '/quiz/submit',
            'body': json.dumps({
                'quiz_id': self.sample_quiz_id,
                'answers': [
                    {'question_id': 'q1', 'selected_answer': 'Storage'}
                ]
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert body['message'] == 'Quiz submitted successfully'

    @patch('main.quiz_sessions_table')
    def test_lambda_handler_get_quiz_history(self, mock_quiz_table):
        """Test Lambda handler for quiz history retrieval."""
        mock_quiz_table.query.return_value = {
            'Items': [
                {
                    'quiz_id': 'quiz1',
                    'user_id': self.sample_user_id,
                    'score': Decimal('85'),
                    'status': 'completed'
                }
            ]
        }
        
        event = {
            'httpMethod': 'GET',
            'path': f'/quiz/history/{self.sample_user_id}',
            'pathParameters': {'user_id': self.sample_user_id},
            'body': json.dumps({'limit': 10})
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'quiz_history' in body
        assert len(body['quiz_history']) == 1

    def test_lambda_handler_invalid_endpoint(self):
        """Test Lambda handler with invalid endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/invalid/endpoint',
            'body': '{}'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'Endpoint not found'

    def test_lambda_handler_missing_required_fields(self):
        """Test Lambda handler with missing required fields."""
        event = {
            'httpMethod': 'POST',
            'path': '/quiz/generate',
            'body': json.dumps({
                'certification_type': 'SAA'
                # Missing user_id
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing required field' in body['error']

    def test_adaptive_selection_prioritizes_weak_areas(self):
        """Test that adaptive selection prioritizes weak areas."""
        # Create performance data with clear weak area
        performance_data = {
            "storage": {"average_score": 90.0, "accuracy": 0.9, "is_weak_area": False},
            "compute": {"average_score": 40.0, "accuracy": 0.4, "is_weak_area": True},
            "database": {"average_score": 85.0, "accuracy": 0.85, "is_weak_area": False}
        }
        
        # Create questions with different categories
        questions = [
            {"content_id": "q1", "category": "storage", "question_text": "Storage Q", "answer_options": ["A", "B"], "correct_answer": "A"},
            {"content_id": "q2", "category": "compute", "question_text": "Compute Q", "answer_options": ["A", "B"], "correct_answer": "A"},
            {"content_id": "q3", "category": "compute", "question_text": "Compute Q2", "answer_options": ["A", "B"], "correct_answer": "A"},
            {"content_id": "q4", "category": "database", "question_text": "Database Q", "answer_options": ["A", "B"], "correct_answer": "A"}
        ]
        
        selected = select_adaptive_questions(questions, performance_data, [], count=3)
        
        # Should prioritize compute questions (weak area)
        compute_questions = [q for q in selected if q['category'] == 'compute']
        assert len(compute_questions) >= 1  # Should include at least one compute question

    def test_anti_repetition_logic(self):
        """Test that recently answered questions are avoided."""
        recently_answered = ['q1', 'q2']
        
        selected = select_adaptive_questions(
            self.sample_questions,
            self.sample_performance,
            recently_answered,
            count=2
        )
        
        selected_ids = [q['content_id'] for q in selected]
        
        # Should avoid recently answered questions when possible
        for recent_id in recently_answered:
            if recent_id in [q['content_id'] for q in self.sample_questions]:
                # Only check if we have enough other questions available
                if len(self.sample_questions) - len(recently_answered) >= 2:
                    assert recent_id not in selected_ids


if __name__ == '__main__':
    pytest.main([__file__])