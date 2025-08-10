# chatbot_lambda_src/main.py

import os
import json
import boto3
import traceback
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from botocore.exceptions import ClientError, BotoCoreError

# Global variables for AWS clients
bedrock_runtime = None
opensearch_client = None
opensearch_endpoint = None
opensearch_index = None
aws_region = None

def initialize_clients():
    """Initialize AWS clients with comprehensive error handling."""
    global bedrock_runtime, opensearch_client, opensearch_endpoint, opensearch_index, aws_region
    
    try:
        # Get environment variables with validation
        opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
        opensearch_index = os.environ.get('OPENSEARCH_INDEX')
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        if not opensearch_endpoint:
            raise ValueError("OPENSEARCH_ENDPOINT environment variable is required")
        if not opensearch_index:
            raise ValueError("OPENSEARCH_INDEX environment variable is required")
        
        # Initialize Bedrock client
        try:
            bedrock_runtime = boto3.client('bedrock-runtime', region_name=aws_region)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Bedrock client: {str(e)}")
        
        # Initialize OpenSearch client
        try:
            host = opensearch_endpoint.replace("https://", "")
            if not host:
                raise ValueError("Invalid OpenSearch endpoint format")
            
            credentials = boto3.Session().get_credentials()
            if not credentials:
                raise RuntimeError("AWS credentials not found")
            
            auth = AWSV4SignerAuth(credentials, aws_region, 'aoss')
            opensearch_client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_timeout=30,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connectivity
            opensearch_client.info()
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenSearch client: {str(e)}")
        
        print("Chatbot clients initialized successfully")
        
    except Exception as e:
        print(f"Critical error initializing chatbot clients: {str(e)}")
        raise

# Initialize clients on module load
try:
    initialize_clients()
except Exception as e:
    print(f"Failed to initialize clients on module load: {e}")
    # Don't raise here to allow Lambda to start

def get_embedding(text):
    """Generates an embedding for a text query with error handling."""
    try:
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")
        
        # Truncate text if too long
        if len(text) > 8000:  # Titan embedding limit
            text = text[:8000]
            print(f"Text truncated to {len(text)} characters for embedding")
        
        body = json.dumps({"inputText": text})
        response = bedrock_runtime.invoke_model(
            body=body, 
            modelId="amazon.titan-embed-text-v1",
            accept="application/json", 
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        
        if not embedding:
            raise RuntimeError("No embedding returned from Bedrock")
        
        if not isinstance(embedding, list) or len(embedding) != 1536:
            raise RuntimeError(f"Invalid embedding format: expected list of 1536 floats, got {type(embedding)} with length {len(embedding) if isinstance(embedding, list) else 'N/A'}")
        
        return embedding
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"Bedrock error generating embedding: {error_code} - {error_msg}")
        raise
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        raise

def search_opensearch(query_embedding, certification_type=None):
    """Searches OpenSearch for relevant document chunks with comprehensive error handling."""
    try:
        if not query_embedding or not isinstance(query_embedding, list):
            raise ValueError("Query embedding must be a non-empty list")
        
        if len(query_embedding) != 1536:
            raise ValueError(f"Query embedding must have 1536 dimensions, got {len(query_embedding)}")
        
        # Build search query with validation
        query = {
            "size": 3,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "vector_field": {
                                    "vector": query_embedding,
                                    "k": 3
                                }
                            }
                        }
                    ]
                }
            },
            "_source": {
                "excludes": ["vector_field"]  # Don't return the large vector field
            }
        }
        
        # Add certification type filter if specified
        if certification_type:
            if not isinstance(certification_type, str):
                raise ValueError("Certification type must be a string")
            
            query["query"]["bool"]["filter"] = [
                {"term": {"certification_type": certification_type}}
            ]
        
        # Perform search with timeout
        response = opensearch_client.search(
            body=query, 
            index=opensearch_index,
            timeout='30s'
        )
        
        if not response or "hits" not in response:
            raise RuntimeError("Invalid search response from OpenSearch")
        
        hits = response["hits"]["hits"]
        if not hits:
            print("No search results found")
            return "", []
        
        # Build structured context with metadata and validation
        context_parts = []
        for i, hit in enumerate(hits):
            try:
                source = hit.get("_source", {})
                text = source.get("text", "")
                
                if not text:
                    print(f"Skipping hit {i}: no text content")
                    continue
                
                # Sanitize and validate text
                text = text.strip()
                if len(text) > 5000:  # Limit context size
                    text = text[:5000] + "..."
                
                context_part = {
                    "text": text,
                    "score": float(hit.get("_score", 0.0)),
                    "content_id": source.get("content_id", "unknown"),
                    "certification_type": source.get("certification_type", "general")
                }
                context_parts.append(context_part)
                
            except Exception as e:
                print(f"Error processing search hit {i}: {str(e)}")
                continue
        
        if not context_parts:
            print("No valid search results after processing")
            return "", []
        
        # Concatenate text for the LLM with size limits
        context_texts = [part["text"] for part in context_parts]
        context = "\n\n".join(context_texts)
        
        # Limit total context size
        if len(context) > 15000:
            context = context[:15000] + "\n\n[Context truncated...]"
        
        print(f"Search completed: {len(context_parts)} results, {len(context)} characters of context")
        return context, context_parts
        
    except Exception as e:
        print(f"OpenSearch search error: {str(e)}")
        raise

def generate_answer(question, context):
    """Generates an answer using the retrieved context and a Bedrock model with error handling."""
    try:
        if not question or not isinstance(question, str):
            raise ValueError("Question must be a non-empty string")
        
        if not context or not isinstance(context, str):
            print("Warning: No context provided, generating answer without context")
            context = "No relevant context found."
        
        # Sanitize inputs
        question = question.strip()
        context = context.strip()
        
        # Limit context size to prevent token limit issues
        max_context_length = 10000
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n\n[Context truncated due to length...]"
        
        # Build prompt with safety instructions
        prompt = f"""Human: You are an AI assistant for professional certifications. Answer the following question based ONLY on the provided context. 

Guidelines:
- If the answer is not in the context, say "I don't have enough information to answer that question."
- Be concise and accurate
- If the context is insufficient, acknowledge this limitation
- Focus on certification-related information

Context:
{context}

Question: {question}
    """Main handler for the chatbot API with comprehensive error handling."""
    print(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        # Validate clients are initialized
        if not _validate_clients():
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "error": "Service temporarily unavailable",
                    "error_type": "ServiceInitializationError"
                })
            }
        
        # Parse and validate the request
        request_data = _parse_and_validate_request(event)
        question = request_data['question']
        certification_type = request_data.get('certification_type')
        
        print(f"Processing question: {question[:100]}...")
        
        # Process the query with comprehensive error handling
        result = _process_query_with_error_handling(question, certification_type)
        
        if result['success']:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "answer": result['answer'],
                    "sources": result.get('sources', []),
                    "certification_type": certification_type
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "error": result['error'],
                    "error_type": result.get('error_type', 'ProcessingError')
                })
            }
        
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "error": str(e),
                "error_type": "ValidationError"
            })
        }
        
    except Exception as e:
        error_msg = f"Unexpected error in chatbot handler: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "error": "An unexpected error occurred",
                "error_type": "InternalError"
            })
        }


def _validate_clients() -> bool:
    """Validate that all required clients are initialized."""
    global bedrock_runtime, opensearch_client
    
    if not bedrock_runtime:
        print("Bedrock client not initialized")
        return False
    if not opensearch_client:
        print("OpenSearch client not initialized")
        return False
    
    return True


def _parse_and_validate_request(event: dict) -> dict:
    """Parse and validate the incoming request."""
    try:
        # Parse request body
        body_str = event.get("body", "{}")
        if isinstance(body_str, str):
            body = json.loads(body_str)
        else:
            body = body_str
        
        # Validate question
        question = body.get("question")
        if not question:
            raise ValueError("Question not provided")
        
        if not isinstance(question, str):
            raise ValueError("Question must be a string")
        
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty")
        
        if len(question) > 1000:
            raise ValueError("Question too long (max 1000 characters)")
        
        # Validate optional certification type
        certification_type = body.get("certification_type")
        if certification_type:
            if not isinstance(certification_type, str):
                raise ValueError("Certification type must be a string")
            
            valid_certs = ['CCP', 'AIP', 'MLA', 'DEA', 'DVA', 'SAA', 'SOA', 'DOP', 'SAP', 'ANS', 'MLS', 'SCS', 'GENERAL']
            if certification_type.upper() not in valid_certs:
                raise ValueError(f"Invalid certification type. Must be one of: {valid_certs}")
            
            certification_type = certification_type.upper()
        
        return {
            'question': question,
            'certification_type': certification_type
        }
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in request body: {str(e)}")
    except Exception as e:
        raise ValueError(f"Request validation failed: {str(e)}")


def _process_query_with_error_handling(question: str, certification_type: str = None) -> dict:
    """Process the query with comprehensive error handling."""
    result = {
        'success': False,
        'answer': None,
        'sources': [],
        'error': None,
        'error_type': None
    }
    
    try:
        # Step 1: Get embedding with retry logic
        query_embedding = _get_embedding_with_retry(question)
        
        # Step 2: Search for context with error handling
        search_result = _search_opensearch_with_error_handling(query_embedding, certification_type)
        
        if not search_result['success']:
            result['error'] = f"Search failed: {search_result['error']}"
            result['error_type'] = 'SearchError'
            return result
        
        retrieved_context = search_result['context']
        context_parts = search_result['context_parts']
        
        # Step 3: Generate answer with retry logic
        answer = _generate_answer_with_retry(question, retrieved_context)
        
        result['success'] = True
        result['answer'] = answer
        result['sources'] = [
            {
                'content_id': part.get('content_id', 'unknown'),
                'score': part.get('score', 0.0),
                'certification_type': part.get('certification_type', 'general')
            }
            for part in context_parts
        ]
        
        return result
        
    except Exception as e:
        error_msg = f"Query processing failed: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        
        result['error'] = error_msg
        result['error_type'] = type(e).__name__
        return result


def _get_embedding_with_retry(text: str, max_retries: int = 3) -> list:
    """Get embedding with retry logic."""
    for attempt in range(max_retries):
        try:
            return get_embedding(text)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['ValidationException', 'AccessDeniedException']:
                # These errors are not retryable
                raise
            
            if attempt == max_retries - 1:
                raise
            
            print(f"Embedding generation attempt {attempt + 1} failed: {error_code}. Retrying...")
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            print(f"Embedding generation attempt {attempt + 1} failed: {str(e)}. Retrying...")
    
    return []


def _search_opensearch_with_error_handling(query_embedding: list, certification_type: str = None) -> dict:
    """Search OpenSearch with comprehensive error handling."""
    result = {
        'success': False,
        'context': '',
        'context_parts': [],
        'error': None
    }
    
    try:
        if not query_embedding:
            result['error'] = 'Invalid query embedding'
            return result
        
        # Perform search with retry logic
        for attempt in range(3):
            try:
                context, context_parts = search_opensearch(query_embedding, certification_type)
                result['success'] = True
                result['context'] = context
                result['context_parts'] = context_parts
                return result
                
            except Exception as e:
                if attempt == 2:  # Last attempt
                    result['error'] = f"Search failed after retries: {str(e)}"
                    return result
                
                print(f"Search attempt {attempt + 1} failed: {str(e)}. Retrying...")
        
        return result
        
    except Exception as e:
        result['error'] = f"Search error: {str(e)}"
        return result


def _generate_answer_with_retry(question: str, context: str, max_retries: int = 3) -> str:
    """Generate answer with retry logic."""
    for attempt in range(max_retries):
        try:
            return generate_answer(question, context)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['ValidationException', 'AccessDeniedException']:
                # These errors are not retryable
                raise
            
            if attempt == max_retries - 1:
                raise
            
            print(f"Answer generation attempt {attempt + 1} failed: {error_code}. Retrying...")
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            print(f"Answer generation attempt {attempt + 1} failed: {str(e)}. Retrying...")