"""
Integration tests for the Quiz Generation Service.

Tests end-to-end quiz workflows including generation, submission,
and progress tracking integration.
"""

import pytest
import json
import boto3
import uuid
import time
from datetime import datetime, timezone
from decimal import Decimal
from moto import mock_dynamodb, mock_opensearch
import os
from unittest.mock import patch, MagicMock


class TestQuizIntegration:
    """Integration test suite for quiz service."""
    
    @pytest.fixture(autouse=True)
    def setup_aws_mocks(self):
        """Set up AWS service mocks."""
        # Mock environment variables
        os.environ['QUIZ_SESSIONS_TABLE'] = 'test-quiz-sessions'
        os.environ['USER_PROGRESS_TABLE'] = 'test-user-progress'
        os.environ['CONTENT_METADATA_TABLE'] = 'test-content-metadata'
        os.environ['OPENSEARCH_ENDPOINT'] = 'https://test-endpoint.us-east-1.aoss.amazonaws.com'
        os.environ['OPENSEARCH_INDEX'] = 'test-index'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        # Start DynamoDB mock
        self.dynamodb_mock = mock_dynamodb()
        self.dynamodb_mock.start()
        
        # Create test tables
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.create_test_tables()
        
        yield
        
        # Clean up
        self.dynamodb_mock.stop()
    
    def create_test_tables(self):
        """Create test DynamoDB tables."""
        # Quiz sessions table
        self.quiz_sessions_table = self.dynamodb.create_table(
            TableName='test-quiz-sessions',
            KeySchema=[
                {'AttributeName': 'quiz_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'quiz_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'started_at', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserQuizIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'started_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        # User progress table
        self.user_progress_table = self.dynamodb.create_table(
            TableName='test-user-progress',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'content_id_certification', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'content_id_certification', 'AttributeType': 'S'},
                {'AttributeName': 'certification_type', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserCertificationIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'certification_type', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        # Content metadata table
        self.content_metadata_table = self.dynamodb.create_table(
            TableName='test-content-metadata',
            KeySchema=[
                {'AttributeName': 'content_id', 'KeyType': 'HASH'},
                {'AttributeName': 'certification_type', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'content_id', 'AttributeType': 'S'},
                {'AttributeName': 'certification_type', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for tables to be created
        self.quiz_sessions_table.wait_until_exists()
        self.user_progress_table.wait_until_exists()
        self.content_metadata_table.wait_until_exists()
    
    def seed_test_data(self):
        """Seed test data into tables."""
        # Add sample user progress data
        progress_items = [
            {
                'user_id': 'test-user-123',
                'content_id_certification': 'q1#SAA',
                'content_id': 'q1',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('85'),
                'category': 'storage',
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            {
                'user_id': 'test-user-123',
                'content_id_certification': 'q2#SAA',
                'content_id': 'q2',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('60'),
                'category': 'compute',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for item in progress_items:
            self.user_progress_table.put_item(Item=item)
    
    @patch('quiz_lambda_src.main.opensearch_client')
    def test_complete_quiz_workflow(self, mock_opensearch):
        """Test complete quiz workflow from generation to submission."""
        # Mock OpenSearch response
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
        
        # Import after mocking
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../quiz_lambda_src'))
        from main import lambda_handler
        
        # Seed test data
        self.seed_test_data()
        
        # Step 1: Generate quiz
        generate_event = {
            'httpMethod': 'POST',
            'path': '/quiz/generate',
            'body': json.dumps({
                'user_id': 'test-user-123',
                'certification_type': 'SAA',
                'question_count': 2,
                'difficulty': 'mixed'
            })
        }
        
        generate_response = lambda_handler(generate_event, {})
        assert generate_response['statusCode'] == 200
        
        generate_body = json.loads(generate_response['body'])
        quiz_id = generate_body['quiz']['quiz_id']
        questions = generate_body['quiz']['questions']
        
        assert len(questions) <= 2
        assert quiz_id is not None
        
        # Verify quiz was stored in database
        stored_quiz = self.quiz_sessions_table.get_item(Key={'quiz_id': quiz_id})
        assert 'Item' in stored_quiz
        assert stored_quiz['Item']['status'] == 'in_progress'
        
        # Step 2: Submit quiz answers
        answers = []
        for question in questions:
            # Submit correct answer for first question, incorrect for others
            if question['question_id'] == questions[0]['question_id']:
                correct_answer = stored_quiz['Item']['questions'][0]['correct_answer']
                answers.append({
                    'question_id': question['question_id'],
                    'selected_answer': correct_answer
                })
            else:
                # Submit incorrect answer
                answers.append({
                    'question_id': question['question_id'],
                    'selected_answer': 'Wrong answer'
                })
        
        submit_event = {
            'httpMethod': 'POST',
            'path': '/quiz/submit',
            'body': json.dumps({
                'quiz_id': quiz_id,
                'answers': answers
            })
        }
        
        submit_response = lambda_handler(submit_event, {})
        assert submit_response['statusCode'] == 200
        
        submit_body = json.loads(submit_response['body'])
        results = submit_body['results']
        
        # Verify scoring
        assert results['total_questions'] == len(questions)
        assert results['correct_answers'] >= 0
        assert 0 <= results['score'] <= 100
        
        # Verify quiz status updated
        updated_quiz = self.quiz_sessions_table.get_item(Key={'quiz_id': quiz_id})
        assert updated_quiz['Item']['status'] == 'completed'
        assert 'score' in updated_quiz['Item']
        
        # Step 3: Verify progress tracking
        # Check that user progress was recorded for each question
        progress_response = self.user_progress_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': 'test-user-123'}
        )
        
        # Should have original progress + new quiz progress
        progress_items = progress_response['Items']
        quiz_progress_items = [
            item for item in progress_items 
            if item.get('session_id') == quiz_id
        ]
        
        assert len(quiz_progress_items) == len(questions)
        
        # Step 4: Get quiz history
        history_event = {
            'httpMethod': 'GET',
            'path': '/quiz/history/test-user-123',
            'pathParameters': {'user_id': 'test-user-123'},
            'body': json.dumps({'limit': 10})
        }
        
        history_response = lambda_handler(history_event, {})
        assert history_response['statusCode'] == 200
        
        history_body = json.loads(history_response['body'])
        quiz_history = history_body['quiz_history']
        
        assert len(quiz_history) >= 1
        assert any(quiz['quiz_id'] == quiz_id for quiz in quiz_history)
    
    @patch('quiz_lambda_src.main.opensearch_client')
    def test_adaptive_question_selection_integration(self, mock_opensearch):
        """Test that adaptive selection works with real performance data."""
        # Mock OpenSearch with questions from different categories
        mock_opensearch.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'content_id': 'storage_q1',
                            'text': '''Question: What is S3? A) Storage B) Compute Answer: A''',
                            'certification_type': 'SAA',
                            'category': 'storage',
                            'difficulty': 'beginner'
                        }
                    },
                    {
                        '_source': {
                            'content_id': 'compute_q1',
                            'text': '''Question: What is EC2? A) Storage B) Compute Answer: B''',
                            'certification_type': 'SAA',
                            'category': 'compute',
                            'difficulty': 'intermediate'
                        }
                    },
                    {
                        '_source': {
                            'content_id': 'compute_q2',
                            'text': '''Question: What is Lambda? A) Storage B) Compute Answer: B''',
                            'certification_type': 'SAA',
                            'category': 'compute',
                            'difficulty': 'intermediate'
                        }
                    }
                ]
            }
        }
        
        # Seed performance data showing weakness in compute
        weak_performance_items = [
            {
                'user_id': 'test-user-weak',
                'content_id_certification': 'storage_old#SAA',
                'content_id': 'storage_old',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('90'),  # Strong in storage
                'category': 'storage',
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            {
                'user_id': 'test-user-weak',
                'content_id_certification': 'compute_old#SAA',
                'content_id': 'compute_old',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('40'),  # Weak in compute
                'category': 'compute',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for item in weak_performance_items:
            self.user_progress_table.put_item(Item=item)
        
        # Import after mocking
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../quiz_lambda_src'))
        from main import lambda_handler
        
        # Generate quiz for user with weak compute performance
        generate_event = {
            'httpMethod': 'POST',
            'path': '/quiz/generate',
            'body': json.dumps({
                'user_id': 'test-user-weak',
                'certification_type': 'SAA',
                'question_count': 2,
                'difficulty': 'mixed'
            })
        }
        
        generate_response = lambda_handler(generate_event, {})
        assert generate_response['statusCode'] == 200
        
        generate_body = json.loads(generate_response['body'])
        questions = generate_body['quiz']['questions']
        
        # Should prioritize compute questions (weak area)
        compute_questions = [q for q in questions if 'compute' in q.get('question_text', '').lower()]
        
        # With adaptive selection, should include compute questions
        assert len(compute_questions) >= 1
    
    @patch('quiz_lambda_src.main.opensearch_client')
    def test_anti_repetition_integration(self, mock_opensearch):
        """Test anti-repetition logic with real data."""
        # Mock OpenSearch with multiple questions
        mock_opensearch.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'content_id': 'recent_q1',
                            'text': '''Question: Recent Q1? A) Yes B) No Answer: A''',
                            'certification_type': 'SAA',
                            'category': 'storage'
                        }
                    },
                    {
                        '_source': {
                            'content_id': 'recent_q2',
                            'text': '''Question: Recent Q2? A) Yes B) No Answer: A''',
                            'certification_type': 'SAA',
                            'category': 'compute'
                        }
                    },
                    {
                        '_source': {
                            'content_id': 'new_q1',
                            'text': '''Question: New Q1? A) Yes B) No Answer: A''',
                            'certification_type': 'SAA',
                            'category': 'database'
                        }
                    }
                ]
            }
        }
        
        # Add recent progress for some questions
        recent_time = datetime.now(timezone.utc).isoformat()
        recent_progress_items = [
            {
                'user_id': 'test-user-recent',
                'content_id_certification': 'recent_q1#SAA',
                'content_id': 'recent_q1',
                'certification_type': 'SAA',
                'progress_type': 'answered',
                'score': Decimal('80'),
                'category': 'storage',
                'timestamp': recent_time
            }
        ]
        
        for item in recent_progress_items:
            self.user_progress_table.put_item(Item=item)
        
        # Import after mocking
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../quiz_lambda_src'))
        from main import lambda_handler
        
        # Generate quiz
        generate_event = {
            'httpMethod': 'POST',
            'path': '/quiz/generate',
            'body': json.dumps({
                'user_id': 'test-user-recent',
                'certification_type': 'SAA',
                'question_count': 2,
                'difficulty': 'mixed'
            })
        }
        
        generate_response = lambda_handler(generate_event, {})
        assert generate_response['statusCode'] == 200
        
        generate_body = json.loads(generate_response['body'])
        questions = generate_body['quiz']['questions']
        
        # Should avoid recently answered questions when possible
        question_ids = [q['question_id'] for q in questions]
        
        # If we have enough non-recent questions, should avoid recent ones
        if len(questions) < 3:  # We have 3 total questions, 1 recent
            assert 'recent_q1' not in question_ids or len(question_ids) == 1
    
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../quiz_lambda_src'))
        from main import lambda_handler
        
        # Test quiz generation with invalid certification
        generate_event = {
            'httpMethod': 'POST',
            'path': '/quiz/generate',
            'body': json.dumps({
                'user_id': 'test-user-123',
                'certification_type': 'INVALID',
                'question_count': 5
            })
        }
        
        # Should handle gracefully when no questions found
        with patch('quiz_lambda_src.main.opensearch_client') as mock_opensearch:
            mock_opensearch.search.return_value = {'hits': {'hits': []}}
            
            generate_response = lambda_handler(generate_event, {})
            assert generate_response['statusCode'] == 400
            
            body = json.loads(generate_response['body'])
            assert 'No questions found' in body['error']
        
        # Test quiz submission with invalid quiz ID
        submit_event = {
            'httpMethod': 'POST',
            'path': '/quiz/submit',
            'body': json.dumps({
                'quiz_id': 'invalid-quiz-id',
                'answers': []
            })
        }
        
        submit_response = lambda_handler(submit_event, {})
        assert submit_response['statusCode'] == 400
        
        body = json.loads(submit_response['body'])
        assert 'Quiz session not found' in body['error']
    
    def test_performance_tracking_accuracy(self):
        """Test that performance tracking accurately reflects quiz results."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../quiz_lambda_src'))
        from main import lambda_handler
        
        # Create a quiz session manually
        quiz_id = str(uuid.uuid4())
        quiz_session = {
            'quiz_id': quiz_id,
            'user_id': 'test-user-perf',
            'certification_type': 'SAA',
            'status': 'in_progress',
            'questions': [
                {
                    'question_id': 'perf_q1',
                    'question_text': 'Test question 1?',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 'A',
                    'explanation': 'A is correct',
                    'category': 'storage'
                },
                {
                    'question_id': 'perf_q2',
                    'question_text': 'Test question 2?',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 'B',
                    'explanation': 'B is correct',
                    'category': 'compute'
                }
            ],
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.quiz_sessions_table.put_item(Item=quiz_session)
        
        # Submit answers (1 correct, 1 incorrect)
        submit_event = {
            'httpMethod': 'POST',
            'path': '/quiz/submit',
            'body': json.dumps({
                'quiz_id': quiz_id,
                'answers': [
                    {'question_id': 'perf_q1', 'selected_answer': 'A'},  # Correct
                    {'question_id': 'perf_q2', 'selected_answer': 'C'}   # Incorrect
                ]
            })
        }
        
        submit_response = lambda_handler(submit_event, {})
        assert submit_response['statusCode'] == 200
        
        # Verify progress tracking
        progress_response = self.user_progress_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': 'test-user-perf'}
        )
        
        progress_items = progress_response['Items']
        assert len(progress_items) == 2
        
        # Check individual scores
        q1_progress = next(item for item in progress_items if item['content_id'] == 'perf_q1')
        q2_progress = next(item for item in progress_items if item['content_id'] == 'perf_q2')
        
        assert float(q1_progress['score']) == 100.0  # Correct answer
        assert float(q2_progress['score']) == 0.0    # Incorrect answer


if __name__ == '__main__':
    pytest.main([__file__])