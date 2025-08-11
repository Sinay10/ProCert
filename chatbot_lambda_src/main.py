# chatbot_lambda_src/main.py

import os
import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Initialize clients and get environment variables
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
opensearch_endpoint = os.environ['OPENSEARCH_ENDPOINT']
opensearch_index = os.environ['OPENSEARCH_INDEX']
conversation_table_name = os.environ['CONVERSATION_TABLE']
aws_region = os.environ['AWS_REGION']

# Set up the OpenSearch client
host = opensearch_endpoint.replace("https://", "")
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, aws_region, 'aoss')
opensearch_client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    pool_timeout=30
)

# DynamoDB table
conversation_table = dynamodb.Table(conversation_table_name)

def get_embedding(text: str) -> List[float]:
    """Generates an embedding for a text query."""
    body = json.dumps({"inputText": text})
    response = bedrock_runtime.invoke_model(
        body=body, modelId="amazon.titan-embed-text-v1",
        accept="application/json", contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")

def search_opensearch(query_embedding: List[float], certification_type: Optional[str] = None, 
                     size: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
    """Searches OpenSearch for relevant document chunks with optional filtering."""
    query = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "knn": {
                            "vector_field": {
                                "vector": query_embedding,
                                "k": size
                            }
                        }
                    }
                ]
            }
        }
    }
    
    # Add certification type filter if specified
    if certification_type:
        query["query"]["bool"]["filter"] = [
            {"term": {"certification_type": certification_type}}
        ]
    
    try:
        response = opensearch_client.search(body=query, index=opensearch_index)
        
        # Build structured context with metadata
        context_parts = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            context_parts.append({
                "text": source["text"],
                "score": hit["_score"],
                "content_id": source.get("content_id", "unknown"),
                "certification_type": source.get("certification_type", "general"),
                "category": source.get("category", ""),
                "source_file": source.get("source_file", "")
            })
            
        # Concatenate text for the LLM
        context = "\n\n".join([part["text"] for part in context_parts])
        return context, context_parts
    
    except Exception as e:
        print(f"Error searching OpenSearch: {e}")
        return "", []

def generate_rag_answer(question: str, context: str, conversation_history: List[Dict] = None) -> str:
    """Generates an answer using only the retrieved context (RAG-only mode)."""
    history_context = ""
    if conversation_history:
        recent_messages = conversation_history[-4:]  # Last 4 messages for context
        history_context = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in recent_messages
        ])
    
    prompt = f"""You are an AI assistant for AWS professional certifications. Answer the following question based ONLY on the provided study materials context. 

Rules:
- Use ONLY the information from the provided context
- If the answer is not in the context, say "I don't have enough information in the study materials to answer that question. Would you like me to use enhanced mode for broader AWS knowledge?"
- Be specific and cite relevant details from the context
- Focus on certification-relevant information

{f"Previous conversation context: {history_context}" if history_context else ""}

Study Materials Context:
{context}

Question: {question}

Answer based only on the study materials:"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    })
    
    try:
        response = bedrock_runtime.invoke_model(
            body=body, modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            accept="application/json", contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        answer = response_body.get("content")[0].get("text")
        return answer
    except Exception as e:
        print(f"Error generating RAG answer: {e}")
        return "I encountered an error processing your question. Please try again."


def generate_enhanced_answer(question: str, context: str, conversation_history: List[Dict] = None) -> str:
    """Generates an enhanced answer using both RAG context and Claude's AWS knowledge."""
    history_context = ""
    if conversation_history:
        recent_messages = conversation_history[-4:]  # Last 4 messages for context
        history_context = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in recent_messages
        ])
    
    prompt = f"""You are an AI assistant for AWS professional certifications with access to both curated study materials and comprehensive AWS knowledge.

Instructions:
- First, use the provided study materials context if relevant
- Then supplement with your comprehensive AWS knowledge for a complete answer
- Clearly distinguish between information from study materials vs. your general AWS knowledge
- Prioritize certification-specific information
- Provide practical, actionable guidance

{f"Previous conversation context: {history_context}" if history_context else ""}

Study Materials Context:
{context if context else "No specific study materials found for this question."}

Question: {question}

Provide a comprehensive answer using both study materials (if available) and your AWS knowledge:"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}]
    })
    
    try:
        response = bedrock_runtime.invoke_model(
            body=body, modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            accept="application/json", contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        answer = response_body.get("content")[0].get("text")
        return answer
    except Exception as e:
        print(f"Error generating enhanced answer: {e}")
        return "I encountered an error processing your question. Please try again."


def determine_response_mode(question: str, context: str, context_parts: List[Dict], 
                          requested_mode: Optional[str] = None) -> str:
    """Determines whether to use RAG-only or enhanced mode based on context quality."""
    if requested_mode == "enhanced":
        return "enhanced"
    
    if requested_mode == "rag":
        return "rag"
    
    # Auto-determine based on context quality
    if not context_parts or len(context_parts) == 0:
        return "enhanced"  # No relevant content found
    
    # Check if we have high-quality, relevant context
    avg_score = sum(part["score"] for part in context_parts) / len(context_parts)
    if avg_score < 0.7:  # Low relevance scores
        return "enhanced"
    
    return "rag"  # Default to RAG-only for good context


def create_conversation(user_id: str, certification_context: Optional[str] = None) -> str:
    """Creates a new conversation and returns the conversation ID."""
    conversation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    ttl = int(now.timestamp()) + (7 * 24 * 60 * 60)  # 7 days from now
    
    conversation_data = {
        'conversation_id': conversation_id,
        'user_id': user_id,
        'messages': [],
        'certification_context': certification_context,
        'preferred_mode': 'rag',
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'ttl': ttl,
        'metadata': {}
    }
    
    try:
        conversation_table.put_item(Item=conversation_data)
        return conversation_id
    except Exception as e:
        print(f"Error creating conversation: {e}")
        raise


def get_conversation(conversation_id: str) -> Optional[Dict]:
    """Retrieves a conversation by ID."""
    try:
        response = conversation_table.get_item(
            Key={'conversation_id': conversation_id}
        )
        return response.get('Item')
    except Exception as e:
        print(f"Error retrieving conversation: {e}")
        return None


def update_conversation(conversation_id: str, new_message: Dict, preferred_mode: str = None) -> bool:
    """Updates a conversation with a new message."""
    try:
        now = datetime.now(timezone.utc)
        
        # Get current conversation
        conversation = get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Add new message
        messages = conversation.get('messages', [])
        messages.append(new_message)
        
        # Update conversation
        update_expression = "SET messages = :messages, updated_at = :updated_at"
        expression_values = {
            ':messages': messages,
            ':updated_at': now.isoformat()
        }
        
        if preferred_mode:
            update_expression += ", preferred_mode = :preferred_mode"
            expression_values[':preferred_mode'] = preferred_mode
        
        conversation_table.update_item(
            Key={'conversation_id': conversation_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        return True
    except Exception as e:
        print(f"Error updating conversation: {e}")
        return False


def delete_conversation(conversation_id: str) -> bool:
    """Deletes a conversation."""
    try:
        conversation_table.delete_item(
            Key={'conversation_id': conversation_id}
        )
        return True
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return False


def get_user_conversations(user_id: str, limit: int = 20) -> List[Dict]:
    """Gets recent conversations for a user."""
    try:
        response = conversation_table.query(
            IndexName='UserConversationIndex',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error retrieving user conversations: {e}")
        return []

def handle_chat_message(event: Dict) -> Dict:
    """Handles chat message requests."""
    try:
        body = json.loads(event.get("body", "{}"))
        
        # Extract request parameters
        message = body.get("message", "").strip()
        certification = body.get("certification")
        requested_mode = body.get("mode")  # 'rag' or 'enhanced'
        conversation_id = body.get("conversation_id")
        user_id = body.get("user_id", "anonymous")
        
        if not message:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Message is required"})
            }
        
        # Create new conversation if not provided
        if not conversation_id:
            conversation_id = create_conversation(user_id, certification)
        
        # Get conversation history
        conversation = get_conversation(conversation_id)
        conversation_history = conversation.get('messages', []) if conversation else []
        
        # Get certification context from conversation if not provided
        if not certification and conversation:
            certification = conversation.get('certification_context')
        
        # 1. Retrieve: Get embedding and search for context
        query_embedding = get_embedding(message)
        context, context_parts = search_opensearch(query_embedding, certification)
        
        # 2. Determine response mode
        mode_used = determine_response_mode(message, context, context_parts, requested_mode)
        
        # 3. Generate response based on mode
        if mode_used == "enhanced":
            response = generate_enhanced_answer(message, context, conversation_history)
        else:
            response = generate_rag_answer(message, context, conversation_history)
        
        # 4. Prepare source information
        sources = []
        for part in context_parts:
            source_info = {
                "content_id": part["content_id"],
                "score": part["score"],
                "certification_type": part["certification_type"]
            }
            if part.get("source_file"):
                source_info["source_file"] = part["source_file"]
            sources.append(source_info)
        
        # 5. Update conversation with new messages
        now = datetime.now(timezone.utc)
        
        # Add user message
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": now.isoformat(),
            "sources": [],
            "mode_used": None,
            "metadata": {"certification": certification}
        }
        
        # Add assistant message
        assistant_message = {
            "role": "assistant",
            "content": response,
            "timestamp": now.isoformat(),
            "sources": [s["content_id"] for s in sources],
            "mode_used": mode_used,
            "metadata": {"context_parts_count": len(context_parts)}
        }
        
        # Update conversation
        update_conversation(conversation_id, user_message)
        update_conversation(conversation_id, assistant_message, mode_used)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                "response": response,
                "sources": sources,
                "mode_used": mode_used,
                "conversation_id": conversation_id,
                "context_quality": {
                    "parts_found": len(context_parts),
                    "avg_score": sum(p["score"] for p in context_parts) / len(context_parts) if context_parts else 0
                }
            })
        }
        
    except Exception as e:
        print(f"Error handling chat message: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "An error occurred processing your message"})
        }


def handle_get_conversation(event: Dict) -> Dict:
    """Handles get conversation requests."""
    try:
        conversation_id = event.get("pathParameters", {}).get("id")
        
        if not conversation_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Conversation ID is required"})
            }
        
        conversation = get_conversation(conversation_id)
        
        if not conversation:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Conversation not found"})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                "conversation": conversation
            })
        }
        
    except Exception as e:
        print(f"Error getting conversation: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "An error occurred retrieving the conversation"})
        }


def handle_delete_conversation(event: Dict) -> Dict:
    """Handles delete conversation requests."""
    try:
        conversation_id = event.get("pathParameters", {}).get("id")
        
        if not conversation_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Conversation ID is required"})
            }
        
        success = delete_conversation(conversation_id)
        
        if not success:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Conversation not found or could not be deleted"})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({"success": True})
        }
        
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "An error occurred deleting the conversation"})
        }


def handler(event, context):
    """Main handler for the enhanced chatbot API."""
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Handle CORS preflight requests
        if event.get("httpMethod") == "OPTIONS":
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                }
            }
        
        # Route based on path and method
        path = event.get("resource", "")
        method = event.get("httpMethod", "")
        
        if path == "/chat/message" and method == "POST":
            return handle_chat_message(event)
        elif path == "/chat/conversation/{id}" and method == "GET":
            return handle_get_conversation(event)
        elif path == "/chat/conversation/{id}" and method == "DELETE":
            return handle_delete_conversation(event)
        elif path == "/query" and method == "POST":
            # Backward compatibility - convert old format to new
            body = json.loads(event.get("body", "{}"))
            question = body.get("question")
            if question:
                # Create a new event format for the new handler
                new_body = {
                    "message": question,
                    "certification": body.get("certification"),
                    "mode": "rag"  # Default to RAG for backward compatibility
                }
                new_event = event.copy()
                new_event["body"] = json.dumps(new_body)
                response = handle_chat_message(new_event)
                
                # Convert response to old format
                if response["statusCode"] == 200:
                    response_data = json.loads(response["body"])
                    old_format = {"answer": response_data.get("response", "")}
                    response["body"] = json.dumps(old_format)
                
                return response
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"error": "Question not provided."})
                }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Endpoint not found"})
            }
        
    except Exception as e:
        print(f"Error in main handler: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "An internal error occurred"})
        }