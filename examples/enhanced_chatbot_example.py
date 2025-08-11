"""
Example script demonstrating the enhanced chatbot service with dual-mode responses.

This script shows how to interact with the enhanced chatbot API endpoints
and demonstrates the different response modes and conversation management features.
"""

import json
import requests
import time
from typing import Dict, Any, Optional


class EnhancedChatbotClient:
    """Client for interacting with the enhanced chatbot API."""
    
    def __init__(self, api_endpoint: str):
        """
        Initialize the chatbot client.
        
        Args:
            api_endpoint: The API Gateway endpoint URL
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def send_message(self, message: str, conversation_id: Optional[str] = None,
                    certification: Optional[str] = None, mode: Optional[str] = None,
                    user_id: str = "demo-user") -> Dict[str, Any]:
        """
        Send a message to the chatbot.
        
        Args:
            message: The message to send
            conversation_id: Optional conversation ID to continue existing conversation
            certification: Optional certification context (e.g., 'SAA', 'DVA')
            mode: Optional response mode ('rag' or 'enhanced')
            user_id: User identifier
            
        Returns:
            API response as dictionary
        """
        payload = {
            'message': message,
            'user_id': user_id
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        if certification:
            payload['certification'] = certification
        if mode:
            payload['mode'] = mode
        
        response = requests.post(
            f"{self.api_endpoint}/chat/message",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Conversation data as dictionary
        """
        response = requests.get(
            f"{self.api_endpoint}/chat/conversation/{conversation_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get conversation: {response.status_code} - {response.text}")
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if successful
        """
        response = requests.delete(
            f"{self.api_endpoint}/chat/conversation/{conversation_id}",
            headers=self.headers
        )
        
        return response.status_code == 200


def demonstrate_rag_mode(client: EnhancedChatbotClient):
    """Demonstrate RAG-only mode functionality."""
    print("=== RAG-Only Mode Demonstration ===")
    print("This mode uses only curated study materials from the knowledge base.\n")
    
    # Send a question that should have good coverage in study materials
    response = client.send_message(
        message="What is Amazon EC2 and what are its key features?",
        certification="SAA",
        mode="rag"
    )
    
    print(f"Question: What is Amazon EC2 and what are its key features?")
    print(f"Mode Used: {response['mode_used']}")
    print(f"Response: {response['response']}")
    print(f"Sources Found: {len(response['sources'])}")
    
    if response['sources']:
        print("Source Details:")
        for i, source in enumerate(response['sources'][:3], 1):
            print(f"  {i}. Content ID: {source['content_id']}")
            print(f"     Relevance Score: {source['score']:.3f}")
            print(f"     Certification: {source['certification_type']}")
    
    print(f"Context Quality: {response['context_quality']['parts_found']} parts found, "
          f"avg score: {response['context_quality']['avg_score']:.3f}")
    print()
    
    return response['conversation_id']


def demonstrate_enhanced_mode(client: EnhancedChatbotClient):
    """Demonstrate enhanced mode functionality."""
    print("=== Enhanced Mode Demonstration ===")
    print("This mode combines study materials with Claude's comprehensive AWS knowledge.\n")
    
    # Send a question that might not be well covered in study materials
    response = client.send_message(
        message="What are the latest AWS AI/ML services announced in 2024?",
        mode="enhanced"
    )
    
    print(f"Question: What are the latest AWS AI/ML services announced in 2024?")
    print(f"Mode Used: {response['mode_used']}")
    print(f"Response: {response['response']}")
    print(f"Sources Found: {len(response['sources'])}")
    print()
    
    return response['conversation_id']


def demonstrate_auto_mode_selection(client: EnhancedChatbotClient):
    """Demonstrate automatic mode selection."""
    print("=== Automatic Mode Selection Demonstration ===")
    print("The system automatically chooses the best mode based on content availability.\n")
    
    questions = [
        ("What is Amazon S3?", "SAA"),  # Should have good study material coverage
        ("How do I optimize costs for my startup's AWS infrastructure?", None),  # Might need enhanced mode
        ("What are EC2 instance families?", "SAA"),  # Should have good coverage
    ]
    
    conversation_id = None
    
    for question, cert in questions:
        response = client.send_message(
            message=question,
            certification=cert,
            conversation_id=conversation_id
        )
        
        conversation_id = response['conversation_id']
        
        print(f"Question: {question}")
        print(f"Auto-selected Mode: {response['mode_used']}")
        print(f"Context Quality: {response['context_quality']['parts_found']} parts, "
              f"avg score: {response['context_quality']['avg_score']:.3f}")
        print(f"Response Preview: {response['response'][:150]}...")
        print()
    
    return conversation_id


def demonstrate_conversation_management(client: EnhancedChatbotClient):
    """Demonstrate conversation context and management."""
    print("=== Conversation Management Demonstration ===")
    print("Shows how conversation context is maintained across messages.\n")
    
    # Start a conversation about EC2
    response1 = client.send_message(
        message="I'm studying for the SAA certification. Can you explain EC2 instances?",
        certification="SAA"
    )
    
    conversation_id = response1['conversation_id']
    print(f"Initial Question: I'm studying for the SAA certification. Can you explain EC2 instances?")
    print(f"Response Preview: {response1['response'][:150]}...")
    print()
    
    # Follow up with a contextual question
    response2 = client.send_message(
        message="What are the different pricing models for them?",
        conversation_id=conversation_id
    )
    
    print(f"Follow-up Question: What are the different pricing models for them?")
    print(f"Response Preview: {response2['response'][:150]}...")
    print("(Note how the system understands 'them' refers to EC2 instances)")
    print()
    
    # Another follow-up
    response3 = client.send_message(
        message="Which pricing model would be best for a web application with variable traffic?",
        conversation_id=conversation_id
    )
    
    print(f"Second Follow-up: Which pricing model would be best for a web application with variable traffic?")
    print(f"Response Preview: {response3['response'][:150]}...")
    print()
    
    # Retrieve the full conversation
    conversation = client.get_conversation(conversation_id)
    print(f"Full Conversation Retrieved:")
    print(f"- Conversation ID: {conversation_id}")
    print(f"- Total Messages: {len(conversation['conversation']['messages'])}")
    print(f"- Certification Context: {conversation['conversation'].get('certification_context', 'None')}")
    print()
    
    return conversation_id


def demonstrate_source_transparency(client: EnhancedChatbotClient):
    """Demonstrate source transparency and citation."""
    print("=== Source Transparency Demonstration ===")
    print("Shows how the system provides clear source attribution.\n")
    
    # Ask a question that should have multiple sources
    response = client.send_message(
        message="What are the security best practices for EC2 instances?",
        certification="SAA",
        mode="rag"
    )
    
    print(f"Question: What are the security best practices for EC2 instances?")
    print(f"Mode Used: {response['mode_used']}")
    print()
    
    if response['sources']:
        print("Detailed Source Information:")
        for i, source in enumerate(response['sources'], 1):
            print(f"Source {i}:")
            print(f"  - Content ID: {source['content_id']}")
            print(f"  - Relevance Score: {source['score']:.3f}")
            print(f"  - Certification Type: {source['certification_type']}")
            if 'source_file' in source:
                print(f"  - Source File: {source.get('source_file', 'N/A')}")
            print()
    
    # Compare with enhanced mode for the same question
    response_enhanced = client.send_message(
        message="What are the security best practices for EC2 instances?",
        certification="SAA",
        mode="enhanced"
    )
    
    print("Same question in Enhanced Mode:")
    print(f"Mode Used: {response_enhanced['mode_used']}")
    print(f"Response includes both study materials and broader AWS knowledge")
    print()


def main():
    """Main demonstration function."""
    # Replace with your actual API Gateway endpoint
    api_endpoint = "https://your-api-gateway-url.amazonaws.com/prod"
    
    print("Enhanced Chatbot Service Demonstration")
    print("=" * 50)
    print(f"API Endpoint: {api_endpoint}")
    print()
    
    # Check if we should use a real endpoint or mock
    if "your-api-gateway-url" in api_endpoint:
        print("⚠️  Please update the api_endpoint variable with your actual API Gateway URL")
        print("   You can find this in the CDK output after deployment.")
        return
    
    client = EnhancedChatbotClient(api_endpoint)
    
    try:
        # Run demonstrations
        conv_id_1 = demonstrate_rag_mode(client)
        time.sleep(1)
        
        conv_id_2 = demonstrate_enhanced_mode(client)
        time.sleep(1)
        
        conv_id_3 = demonstrate_auto_mode_selection(client)
        time.sleep(1)
        
        conv_id_4 = demonstrate_conversation_management(client)
        time.sleep(1)
        
        demonstrate_source_transparency(client)
        
        # Clean up conversations
        print("=== Cleanup ===")
        conversations_to_delete = [conv_id_1, conv_id_2, conv_id_3, conv_id_4]
        for conv_id in conversations_to_delete:
            if conv_id:
                try:
                    client.delete_conversation(conv_id)
                    print(f"Deleted conversation: {conv_id}")
                except Exception as e:
                    print(f"Failed to delete conversation {conv_id}: {e}")
        
        print("\nDemonstration completed successfully! ✅")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        print("Make sure your API Gateway is deployed and accessible.")


if __name__ == "__main__":
    main()