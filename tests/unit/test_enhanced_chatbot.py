"""
Unit tests for the enhanced chatbot service with dual-mode response system.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import sys
import os

# Add the chatbot source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../chatbot_lambda_src'))

# Mock environment variables before importing
os.environ['OPENSEARCH_ENDPOINT'] = 'https://test-endpoint.us-east-1.aoss.amazonaws.com'
os.environ['OPENSEARCH_INDEX'] = 'test-index'
os.environ['CONVERSATION_TABLE'] = 'test-conversations'
os.environ['AWS_REGION'] = 'us-east-1'

import main


class TestEmbeddingGeneration:
    """Test embedding generation functionality."""
    
    @patch('main.bedrock_runtime')
    def test_get_embedding_success(self, mock_bedrock):
        """Test successful embedding generation."""
        # Mock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'embedding': [0.1, 0.2, 0.3]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Test
        result = main.get_embedding("test query")
        
        # Assertions
        assert result == [0.1, 0.2, 0.3]
        mock_bedrock.invoke_model.assert_called_once()
        
    @patch('main.bedrock_runtime')
    def test_get_embedding_error(self, mock_bedrock):
        """Test embedding generation error handling."""
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock error")
        
        with pytest.raises(Exception):
            main.get_embedding("test query")


class TestOpenSearchOperations:
    """Test OpenSearch search functionality."""
    
    @patch('main.opensearch_client')
    def test_search_opensearch_success(self, mock_client):
        """Test successful OpenSearch query."""
        # Mock response
        mock_response = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'text': 'Test content 1',
                            'content_id': 'content-1',
                            'certification_type': 'SAA',
                            'category': 'EC2',
                            'source_file': 'test1.pdf'
                        },
                        '_score': 0.95
                    },
                    {
                        '_source': {
                            'text': 'Test content 2',
                            'content_id': 'content-2',
                            'certification_type': 'SAA',
                            'category': 'S3'
                        },
                        '_score': 0.87
                    }
                ]
            }
        }
        mock_client.search.return_value = mock_response
        
        # Test
        context, context_parts = main.search_opensearch([0.1, 0.2, 0.3], "SAA")
        
        # Assertions
        assert "Test content 1" in context
        assert "Test content 2" in context
        assert len(context_parts) == 2
        assert context_parts[0]['score'] == 0.95
        assert context_parts[0]['certification_type'] == 'SAA'
        assert context_parts[0]['source_file'] == 'test1.pdf'
        
    @patch('main.opensearch_client')
    def test_search_opensearch_error(self, mock_client):
        """Test OpenSearch error handling."""
        mock_client.search.side_effect = Exception("OpenSearch error")
        
        context, context_parts = main.search_opensearch([0.1, 0.2, 0.3])
        
        assert context == ""
        assert context_parts == []


class TestResponseGeneration:
    """Test response generation in both modes."""
    
    @patch('main.bedrock_runtime')
    def test_generate_rag_answer_success(self, mock_bedrock):
        """Test RAG-only answer generation."""
        # Mock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'This is a RAG-based answer.'}]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Test
        result = main.generate_rag_answer(
            "What is EC2?", 
            "EC2 is a web service that provides compute capacity.",
            []
        )
        
        # Assertions
        assert result == "This is a RAG-based answer."
        mock_bedrock.invoke_model.assert_called_once()
        
    @patch('main.bedrock_runtime')
    def test_generate_enhanced_answer_success(self, mock_bedrock):
        """Test enhanced answer generation."""
        # Mock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'This is an enhanced answer with broader AWS knowledge.'}]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Test
        result = main.generate_enhanced_answer(
            "What is EC2?", 
            "EC2 is a web service that provides compute capacity.",
            []
        )
        
        # Assertions
        assert result == "This is an enhanced answer with broader AWS knowledge."
        mock_bedrock.invoke_model.assert_called_once()
        
    @patch('main.bedrock_runtime')
    def test_generate_answer_with_conversation_history(self, mock_bedrock):
        """Test answer generation with conversation history."""
        # Mock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Answer considering conversation history.'}]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Test with conversation history
        history = [
            {'role': 'user', 'content': 'What is AWS?'},
            {'role': 'assistant', 'content': 'AWS is Amazon Web Services.'}
        ]
        
        result = main.generate_rag_answer("Tell me more about EC2", "EC2 context", history)
        
        # Assertions
        assert result == "Answer considering conversation history."
        # Verify that conversation history was included in the prompt
        call_args = mock_bedrock.invoke_model.call_args
        prompt = json.loads(call_args[1]['body'])['messages'][0]['content']
        assert 'User: What is AWS?' in prompt
        assert 'Assistant: AWS is Amazon Web Services.' in prompt


class TestModeSelection:
    """Test intelligent mode selection logic."""
    
    def test_determine_response_mode_explicit_enhanced(self):
        """Test explicit enhanced mode request."""
        result = main.determine_response_mode(
            "test question", 
            "test context", 
            [{'score': 0.9}], 
            "enhanced"
        )
        assert result == "enhanced"
        
    def test_determine_response_mode_explicit_rag(self):
        """Test explicit RAG mode request."""
        result = main.determine_response_mode(
            "test question", 
            "test context", 
            [{'score': 0.9}], 
            "rag"
        )
        assert result == "rag"
        
    def test_determine_response_mode_auto_no_context(self):
        """Test auto mode selection with no context."""
        result = main.determine_response_mode(
            "test question", 
            "", 
            [], 
            None
        )
        assert result == "enhanced"
        
    def test_determine_response_mode_auto_low_quality(self):
        """Test auto mode selection with low quality context."""
        result = main.determine_response_mode(
            "test question", 
            "test context", 
            [{'score': 0.5}, {'score': 0.6}], 
            None
        )
        assert result == "enhanced"
        
    def test_determine_response_mode_auto_high_quality(self):
        """Test auto mode selection with high quality context."""
        result = main.determine_response_mode(
            "test question", 
            "test context", 
            [{'score': 0.8}, {'score': 0.9}], 
            None
        )
        assert result == "rag"


class TestConversationManagement:
    """Test conversation management functionality."""
    
    @patch('main.conversation_table')
    def test_create_conversation_success(self, mock_table):
        """Test successful conversation creation."""
        mock_table.put_item.return_value = {}
        
        result = main.create_conversation("user123", "SAA")
        
        # Assertions
        assert result is not None
        assert len(result) == 36  # UUID length
        mock_table.put_item.assert_called_once()
        
        # Check the item structure
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['user_id'] == "user123"
        assert item['certification_context'] == "SAA"
        assert item['preferred_mode'] == 'rag'
        assert 'ttl' in item
        
    @patch('main.conversation_table')
    def test_get_conversation_success(self, mock_table):
        """Test successful conversation retrieval."""
        mock_conversation = {
            'conversation_id': 'conv-123',
            'user_id': 'user123',
            'messages': [],
            'certification_context': 'SAA'
        }
        mock_table.get_item.return_value = {'Item': mock_conversation}
        
        result = main.get_conversation('conv-123')
        
        assert result == mock_conversation
        mock_table.get_item.assert_called_once_with(
            Key={'conversation_id': 'conv-123'}
        )
        
    @patch('main.conversation_table')
    def test_get_conversation_not_found(self, mock_table):
        """Test conversation not found."""
        mock_table.get_item.return_value = {}
        
        result = main.get_conversation('nonexistent')
        
        assert result is None
        
    @patch('main.conversation_table')
    @patch('main.get_conversation')
    def test_update_conversation_success(self, mock_get, mock_table):
        """Test successful conversation update."""
        # Mock existing conversation
        mock_get.return_value = {
            'conversation_id': 'conv-123',
            'messages': [{'role': 'user', 'content': 'Hello'}]
        }
        mock_table.update_item.return_value = {}
        
        new_message = {'role': 'assistant', 'content': 'Hi there!'}
        result = main.update_conversation('conv-123', new_message, 'rag')
        
        assert result is True
        mock_table.update_item.assert_called_once()
        
    @patch('main.conversation_table')
    def test_delete_conversation_success(self, mock_table):
        """Test successful conversation deletion."""
        mock_table.delete_item.return_value = {}
        
        result = main.delete_conversation('conv-123')
        
        assert result is True
        mock_table.delete_item.assert_called_once_with(
            Key={'conversation_id': 'conv-123'}
        )


class TestAPIHandlers:
    """Test API handler functions."""
    
    @patch('main.create_conversation')
    @patch('main.get_embedding')
    @patch('main.search_opensearch')
    @patch('main.generate_rag_answer')
    @patch('main.update_conversation')
    def test_handle_chat_message_new_conversation(self, mock_update, mock_generate, 
                                                 mock_search, mock_embedding, mock_create):
        """Test chat message handling with new conversation."""
        # Setup mocks
        mock_create.return_value = 'new-conv-123'
        mock_embedding.return_value = [0.1, 0.2, 0.3]
        mock_search.return_value = ("Test context", [{'score': 0.9, 'content_id': 'test-1', 'certification_type': 'SAA'}])
        mock_generate.return_value = "Test response"
        mock_update.return_value = True
        
        # Test event
        event = {
            'body': json.dumps({
                'message': 'What is EC2?',
                'certification': 'SAA',
                'user_id': 'user123'
            })
        }
        
        result = main.handle_chat_message(event)
        
        # Assertions
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['response'] == "Test response"
        assert response_body['conversation_id'] == 'new-conv-123'
        assert response_body['mode_used'] == 'rag'
        assert len(response_body['sources']) == 1
        
    @patch('main.get_conversation')
    def test_handle_get_conversation_success(self, mock_get):
        """Test successful conversation retrieval."""
        mock_conversation = {
            'conversation_id': 'conv-123',
            'user_id': 'user123',
            'messages': []
        }
        mock_get.return_value = mock_conversation
        
        event = {
            'pathParameters': {'id': 'conv-123'}
        }
        
        result = main.handle_get_conversation(event)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['conversation'] == mock_conversation
        
    @patch('main.get_conversation')
    def test_handle_get_conversation_not_found(self, mock_get):
        """Test conversation not found."""
        mock_get.return_value = None
        
        event = {
            'pathParameters': {'id': 'nonexistent'}
        }
        
        result = main.handle_get_conversation(event)
        
        assert result['statusCode'] == 404
        
    @patch('main.delete_conversation')
    def test_handle_delete_conversation_success(self, mock_delete):
        """Test successful conversation deletion."""
        mock_delete.return_value = True
        
        event = {
            'pathParameters': {'id': 'conv-123'}
        }
        
        result = main.handle_delete_conversation(event)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['success'] is True
        
    def test_handle_chat_message_missing_message(self):
        """Test chat message handling with missing message."""
        event = {
            'body': json.dumps({
                'user_id': 'user123'
            })
        }
        
        result = main.handle_chat_message(event)
        
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'error' in response_body


class TestMainHandler:
    """Test the main handler routing."""
    
    def test_handler_cors_preflight(self):
        """Test CORS preflight request handling."""
        event = {
            'httpMethod': 'OPTIONS'
        }
        
        result = main.handler(event, {})
        
        assert result['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in result['headers']
        
    @patch('main.handle_chat_message')
    def test_handler_chat_message_route(self, mock_handle):
        """Test routing to chat message handler."""
        mock_handle.return_value = {'statusCode': 200, 'body': '{}'}
        
        event = {
            'resource': '/chat/message',
            'httpMethod': 'POST',
            'body': json.dumps({'message': 'test'})
        }
        
        result = main.handler(event, {})
        
        assert result['statusCode'] == 200
        mock_handle.assert_called_once_with(event)
        
    @patch('main.handle_get_conversation')
    def test_handler_get_conversation_route(self, mock_handle):
        """Test routing to get conversation handler."""
        mock_handle.return_value = {'statusCode': 200, 'body': '{}'}
        
        event = {
            'resource': '/chat/conversation/{id}',
            'httpMethod': 'GET',
            'pathParameters': {'id': 'conv-123'}
        }
        
        result = main.handler(event, {})
        
        assert result['statusCode'] == 200
        mock_handle.assert_called_once_with(event)
        
    def test_handler_unknown_route(self):
        """Test handling of unknown routes."""
        event = {
            'resource': '/unknown',
            'httpMethod': 'GET'
        }
        
        result = main.handler(event, {})
        
        assert result['statusCode'] == 404
        
    @patch('main.handle_chat_message')
    def test_handler_backward_compatibility(self, mock_handle):
        """Test backward compatibility with old /query endpoint."""
        mock_handle.return_value = {
            'statusCode': 200, 
            'body': json.dumps({'response': 'Test answer'})
        }
        
        event = {
            'resource': '/query',
            'httpMethod': 'POST',
            'body': json.dumps({'question': 'What is EC2?'})
        }
        
        result = main.handler(event, {})
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'answer' in response_body  # Old format


class TestIntegration:
    """Integration tests for the complete flow."""
    
    @patch('main.conversation_table')
    @patch('main.bedrock_runtime')
    @patch('main.opensearch_client')
    def test_complete_chat_flow(self, mock_opensearch, mock_bedrock, mock_table):
        """Test complete chat flow from message to response."""
        # Setup mocks
        mock_table.put_item.return_value = {}
        mock_table.get_item.return_value = {'Item': {'messages': []}}
        mock_table.update_item.return_value = {}
        
        # Mock embedding generation
        embedding_response = {'body': Mock()}
        embedding_response['body'].read.return_value = json.dumps({
            'embedding': [0.1, 0.2, 0.3]
        }).encode()
        
        # Mock answer generation
        answer_response = {'body': Mock()}
        answer_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'EC2 is Amazon Elastic Compute Cloud.'}]
        }).encode()
        
        mock_bedrock.invoke_model.side_effect = [embedding_response, answer_response]
        
        # Mock OpenSearch
        mock_opensearch.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'text': 'EC2 provides scalable compute capacity',
                            'content_id': 'ec2-guide-1',
                            'certification_type': 'SAA'
                        },
                        '_score': 0.95
                    }
                ]
            }
        }
        
        # Test event
        event = {
            'resource': '/chat/message',
            'httpMethod': 'POST',
            'body': json.dumps({
                'message': 'What is EC2?',
                'certification': 'SAA',
                'user_id': 'user123'
            })
        }
        
        result = main.handler(event, {})
        
        # Assertions
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['response'] == 'EC2 is Amazon Elastic Compute Cloud.'
        assert response_body['mode_used'] == 'rag'
        assert len(response_body['sources']) == 1
        assert response_body['sources'][0]['content_id'] == 'ec2-guide-1'


if __name__ == '__main__':
    pytest.main([__file__])