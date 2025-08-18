#!/usr/bin/env python3
"""
Test Direct KNN Query

Test the KNN query structure directly against OpenSearch.
"""

import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def test_direct_knn():
    """Test direct KNN query."""
    print("🔍 Testing direct KNN query...")
    
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
        
        # Generate embedding for "What is AWS Lambda?"
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
        query_embedding = response_body.get("embedding")
        
        if not query_embedding:
            print("   ❌ Failed to generate embedding")
            return
        
        print(f"   ✅ Generated embedding: {len(query_embedding)} dimensions")
        
        # Test different query structures
        query_structures = [
            {
                "name": "Simple KNN (current chatbot structure)",
                "query": {
                    "size": 5,
                    "query": {
                        "knn": {
                            "vector_field": {
                                "vector": query_embedding,
                                "k": 5
                            }
                        }
                    }
                }
            },
            {
                "name": "Bool with KNN (old chatbot structure)",
                "query": {
                    "size": 5,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "knn": {
                                        "vector_field": {
                                            "vector": query_embedding,
                                            "k": 5
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            {
                "name": "KNN at root level",
                "query": {
                    "size": 5,
                    "knn": {
                        "vector_field": {
                            "vector": query_embedding,
                            "k": 5
                        }
                    }
                }
            }
        ]
        
        for test_case in query_structures:
            print(f"\n   🧪 Testing: {test_case['name']}")
            
            try:
                response = client.search(
                    index=index_name,
                    body=test_case['query']
                )
                
                hits = response.get('hits', {}).get('hits', [])
                print(f"      📊 Results: {len(hits)} documents")
                
                if hits:
                    for i, hit in enumerate(hits[:2], 1):
                        source = hit['_source']
                        score = hit['_score']
                        text_preview = source.get('text', '')[:100] + "..."
                        cert_type = source.get('certification_type', 'unknown')
                        
                        print(f"      {i}. Score: {score:.6f}, Cert: {cert_type}")
                        print(f"         Text: {text_preview}")
                    
                    # Calculate average score
                    avg_score = sum(hit['_score'] for hit in hits) / len(hits)
                    print(f"      📊 Average score: {avg_score:.6f}")
                    
                    # Check against thresholds
                    if avg_score < 0.01:  # L2 threshold (lower is better)
                        print(f"      ✅ Passes L2 threshold (< 0.01)")
                    else:
                        print(f"      ❌ Fails L2 threshold (>= 0.01)")
                else:
                    print(f"      ❌ No results found")
                    
            except Exception as e:
                print(f"      ❌ Query failed: {str(e)}")
        
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_direct_knn()