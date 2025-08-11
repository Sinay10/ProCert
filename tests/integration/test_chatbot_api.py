"""
Integration tests for the enhanced chatbot API endpoints.
These tests can be run against a deployed API Gateway endpoint.
"""

import json
import requests
import pytest
import os
from typing import Dict, Any


class TestChatbotAPI:
    """Integration tests for chatbot API endpoints."""
    
    def __init__(self):
        # Get API endpoint from environment or use default for local testing
        self.api_endpoint = os.environ.get('API_ENDPOINT', 'https://your-api-gateway-url.amazonaws.com/prod')
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def test_chat_message_new_conversation(self):
        """Test sending a message to create a new conversation."""
        payload = {
            'message': 'What is Amazon EC2?',
            'certification': 'SAA',
            'user_id': 'test-user-123'
        }
        
        response = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'response' in data
        assert 'conversation_id' in data
        assert 'mode_used' in data
        assert 'sources' in data
        assert 'context_quality' in data
        
        # Verify conversation ID is valid UUID format
        conversation_id = data['conversation_id']
        assert len(conversation_id) == 36
        assert conversation_id.count('-') == 4
        
        return conversation_id
    
    def test_chat_message_existing_conversation(self):
        """Test sending a message to an existing conversation."""
        # First create a conversation
        conversation_id = self.test_chat_message_new_conversation()
        
        # Send follow-up message
        payload = {
            'message': 'What are the different EC2 instance types?',
            'conversation_id': conversation_id,
            'user_id': 'test-user-123'
        }
        
        response = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify same conversation ID is returned
        assert data['conversation_id'] == conversation_id
        assert 'response' in data
    
    def test_chat_message_enhanced_mode(self):
        """Test requesting enhanced mode explicitly."""
        payload = {
            'message': 'What are the latest AWS services announced in 2024?',
            'mode': 'enhanced',
            'user_id': 'test-user-123'
        }
        
        response = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use enhanced mode for this type of question
        assert data['mode_used'] == 'enhanced'
    
    def test_chat_message_rag_mode(self):
        """Test requesting RAG-only mode explicitly."""
        payload = {
            'message': 'What is EC2?',
            'mode': 'rag',
            'certification': 'SAA',
            'user_id': 'test-user-123'
        }
        
        response = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should respect the requested mode
        assert data['mode_used'] == 'rag'
    
    def test_get_conversation(self):
        """Test retrieving a conversation."""
        # First create a conversation
        conversation_id = self.test_chat_message_new_conversation()
        
        # Retrieve the conversation
        response = requests.get(
            f"{self.api_endpoint}/chat/conversation/{conversation_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify conversation structure
        assert 'conversation' in data
        conversation = data['conversation']
        assert conversation['conversation_id'] == conversation_id
        assert 'messages' in conversation
        assert 'user_id' in conversation
        assert len(conversation['messages']) >= 2  # User message + assistant response
    
    def test_get_nonexistent_conversation(self):
        """Test retrieving a non-existent conversation."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = requests.get(
            f"{self.api_endpoint}/chat/conversation/{fake_id}",
            headers=self.headers
        )
        
        assert response.status_code == 404
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # First create a conversation
        conversation_id = self.test_chat_message_new_conversation()
        
        # Delete the conversation
        response = requests.delete(
            f"{self.api_endpoint}/chat/conversation/{conversation_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        
        # Verify conversation is deleted
        get_response = requests.get(
            f"{self.api_endpoint}/chat/conversation/{conversation_id}",
            headers=self.headers
        )
        assert get_response.status_code == 404
    
    def test_backward_compatibility_query_endpoint(self):
        """Test backward compatibility with the old /query endpoint."""
        payload = {
            'question': 'What is Amazon S3?'
        }
        
        response = requests.post(
            f"{self.api_endpoint}/query",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return old format
        assert 'answer' in data
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = requests.options(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers
        )
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
    
    def test_error_handling_missing_message(self):
        """Test error handling for missing message."""
        payload = {
            'user_id': 'test-user-123'
            # Missing 'message' field
        }
        
        response = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
    
    def test_error_handling_invalid_json(self):
        """Test error handling for invalid JSON."""
        response = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            data="invalid json"
        )
        
        assert response.status_code == 400 or response.status_code == 500
    
    def test_conversation_context_persistence(self):
        """Test that conversation context is maintained across messages."""
        # Create conversation with first message
        payload1 = {
            'message': 'I want to learn about EC2 instances',
            'certification': 'SAA',
            'user_id': 'test-user-123'
        }
        
        response1 = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload1
        )
        
        assert response1.status_code == 200
        conversation_id = response1.json()['conversation_id']
        
        # Send follow-up message that relies on context
        payload2 = {
            'message': 'What are the pricing models for them?',
            'conversation_id': conversation_id,
            'user_id': 'test-user-123'
        }
        
        response2 = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload2
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Response should understand "them" refers to EC2 instances
        assert 'pricing' in data2['response'].lower() or 'cost' in data2['response'].lower()


def run_integration_tests():
    """Run all integration tests."""
    if not os.environ.get('API_ENDPOINT'):
        print("Warning: API_ENDPOINT not set. Using default URL.")
        print("Set API_ENDPOINT environment variable to test against deployed API.")
    
    test_suite = TestChatbotAPI()
    
    # List of test methods
    test_methods = [
        'test_chat_message_new_conversation',
        'test_chat_message_existing_conversation',
        'test_chat_message_enhanced_mode',
        'test_chat_message_rag_mode',
        'test_get_conversation',
        'test_get_nonexistent_conversation',
        'test_delete_conversation',
        'test_backward_compatibility_query_endpoint',
        'test_cors_headers',
        'test_error_handling_missing_message',
        'test_error_handling_invalid_json',
        'test_conversation_context_persistence'
    ]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"Running {method_name}...")
            method = getattr(test_suite, method_name)
            method()
            print(f"✓ {method_name} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name} failed: {str(e)}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)