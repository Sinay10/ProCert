#!/usr/bin/env python3
"""
Check Vector Field Structure

Check the actual structure of documents in OpenSearch to see the vector field name.
"""

import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def check_vector_field():
    """Check the vector field structure in OpenSearch documents."""
    print("🔍 Checking vector field structure...")
    
    try:
        # Get OpenSearch client
        with open('cdk-outputs.json', 'r') as f:
            outputs = json.load(f)
        
        stack_outputs = outputs.get("ProcertInfrastructureStack", {})
        opensearch_endpoint = stack_outputs.get('OpenSearchCollectionEndpoint')
        
        host = opensearch_endpoint.replace("https://", "")
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, 'us-east-1', 'aoss')
        
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_timeout=30
        )
        
        index_name = 'procert-vector-collection'
        
        # Get a sample document to see its structure
        print("\n   🔍 Getting sample document structure...")
        try:
            response = client.search(
                index=index_name,
                body={
                    "size": 1,
                    "query": {"match_all": {}}
                }
            )
            
            if response['hits']['hits']:
                sample_doc = response['hits']['hits'][0]['_source']
                
                print(f"      📋 Document fields: {list(sample_doc.keys())}")
                
                # Check for vector fields
                vector_fields = []
                for field_name, field_value in sample_doc.items():
                    if isinstance(field_value, list) and len(field_value) > 100:  # Likely a vector
                        vector_fields.append(field_name)
                        print(f"      🔢 Vector field '{field_name}': {len(field_value)} dimensions")
                        print(f"         First 5 values: {field_value[:5]}")
                
                if not vector_fields:
                    print("      ❌ No vector fields found!")
                    print("      📋 All fields and their types:")
                    for field_name, field_value in sample_doc.items():
                        field_type = type(field_value).__name__
                        if isinstance(field_value, list):
                            field_type += f"[{len(field_value)}]"
                        elif isinstance(field_value, str):
                            field_type += f"({len(field_value)} chars)"
                        print(f"         - {field_name}: {field_type}")
                
                # Test the vector search with the correct field name
                if vector_fields:
                    print(f"\n   🔍 Testing vector search with field '{vector_fields[0]}'...")
                    
                    # Generate a test embedding
                    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
                    
                    query_text = "What is AWS Lambda?"
                    body = json.dumps({"inputText": query_text})
                    
                    response = bedrock_runtime.invoke_model(
                        body=body,
                        modelId="amazon.titan-embed-text-v1",
                        accept="application/json",
                        contentType="application/json"
                    )
                    
                    response_body = json.loads(response.get("body").read())
                    embedding = response_body.get("embedding")
                    
                    if embedding:
                        # Try vector search with the correct field name
                        vector_field_name = vector_fields[0]
                        
                        vector_response = client.search(
                            index=index_name,
                            body={
                                "size": 3,
                                "query": {
                                    "knn": {
                                        vector_field_name: {
                                            "vector": embedding,
                                            "k": 3
                                        }
                                    }
                                }
                            }
                        )
                        
                        vector_hits = vector_response['hits']['hits']
                        print(f"      📊 Vector search found {len(vector_hits)} results")
                        
                        for i, hit in enumerate(vector_hits, 1):
                            source = hit['_source']
                            score = hit['_score']
                            text_preview = source.get('text', '')[:100] + "..."
                            cert_type = source.get('certification_type', 'unknown')
                            
                            print(f"      {i}. Score: {score:.6f}, Cert: {cert_type}")
                            print(f"         Text: {text_preview}")
                            print()
                            
                        # Check if scores are above the chatbot threshold
                        if vector_hits:
                            avg_score = sum(hit['_score'] for hit in vector_hits) / len(vector_hits)
                            print(f"      📊 Average score: {avg_score:.6f}")
                            print(f"      🎯 Chatbot threshold: 0.7")
                            if avg_score >= 0.7:
                                print(f"      ✅ Scores above threshold - should work!")
                            else:
                                print(f"      ❌ Scores below threshold - will fallback to enhanced mode")
                
            else:
                print("      ❌ No documents found")
                
        except Exception as e:
            print(f"      ❌ Document structure check failed: {str(e)}")
            
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")

if __name__ == "__main__":
    check_vector_field()