# chatbot_lambda_src/main.py

import os
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Initialize clients and get environment variables
bedrock_runtime = boto3.client('bedrock-runtime')
opensearch_endpoint = os.environ['OPENSEARCH_ENDPOINT']
opensearch_index = os.environ['OPENSEARCH_INDEX']
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

def get_embedding(text):
    """Generates an embedding for a text query."""
    body = json.dumps({"inputText": text})
    response = bedrock_runtime.invoke_model(
        body=body, modelId="amazon.titan-embed-text-v1",
        accept="application/json", contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")

def search_opensearch(query_embedding, certification_type=None):
    """Searches OpenSearch for relevant document chunks with optional filtering."""
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
        }
    }
    
    # Add certification type filter if specified
    if certification_type:
        query["query"]["bool"]["filter"] = [
            {"term": {"certification_type": certification_type}}
        ]
    
    response = opensearch_client.search(body=query, index=opensearch_index)
    
    # Build structured context with metadata
    context_parts = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        context_parts.append({
            "text": source["text"],
            "score": hit["_score"],
            "content_id": source.get("content_id", "unknown"),
            "certification_type": source.get("certification_type", "general")
        })
        
    # Concatenate text for the LLM
    context = "\n".join([part["text"] for part in context_parts])
    return context, context_parts

def generate_answer(question, context):
    """Generates an answer using the retrieved context and a Bedrock model."""
    prompt = f"""
    Human: You are an AI assistant for professional certifications. Answer the following question based ONLY on the provided context. If the answer is not in the context, say "I don't have enough information to answer that question."

    Context:
    {context}

    Question: {question}

    Assistant:
    """
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    })
    
    response = bedrock_runtime.invoke_model(
        body=body, modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        accept="application/json", contentType="application/json"
    )
    
    response_body = json.loads(response.get("body").read())
    answer = response_body.get("content")[0].get("text")
    return answer

def handler(event, context):
    """Main handler for the chatbot API."""
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse the user's question from the request body
        body = json.loads(event.get("body", "{}"))
        question = body.get("question")

        if not question:
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Question not provided."})
            }

        # 1. Retrieve: Get embedding and search for context
        query_embedding = get_embedding(question)
        retrieved_context = search_opensearch(query_embedding)
        
        # 2. Generate: Create an answer based on the context
        answer = generate_answer(question, retrieved_context)
        
        return {
            'statusCode': 200,
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({"answer": answer})
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": "An error occurred."})
        }