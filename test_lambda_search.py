#!/usr/bin/env python3
"""
Test Lambda Search

This script tests if we can find Lambda-related content in OpenSearch.
"""

import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def test_lambda_search():
    """Test searching for Lambda content."""
    print("🔍 Testing Lambda content search...")
    
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
        
        # Test 1: Simple text search for "Lambda"
        print("\n   🔍 Testing simple text search for 'Lambda'...")
        try:
            response = client.search(
                index=index_name,
                body={
                    "size": 5,
                    "query": {
                        "match": {
                            "text": "Lambda"
                        }
                    }
                }
            )
            
            hits = response['hits']['hits']
            print(f"      📊 Found {len(hits)} results")
            
            for i, hit in enumerate(hits[:3], 1):
                source = hit['_source']
                score = hit['_score']
                text_preview = source.get('text', '')[:200] + "..."
                cert_type = source.get('certification_type', 'unknown')
                
                print(f"      {i}. Score: {score:.3f}, Cert: {cert_type}")
                print(f"         Text: {text_preview}")
                print()
                
        except Exception as e:
            print(f"      ❌ Text search failed: {str(e)}")
        
        # Test 2: Search for "AWS Lambda" specifically
        print("   🔍 Testing search for 'AWS Lambda'...")
        try:
            response = client.search(
                index=index_name,
                body={
                    "size": 5,
                    "query": {
                        "match_phrase": {
                            "text": "AWS Lambda"
                        }
                    }
                }
            )
            
            hits = response['hits']['hits']
            print(f"      📊 Found {len(hits)} results for 'AWS Lambda'")
            
            for i, hit in enumerate(hits[:2], 1):
                source = hit['_source']
                score = hit['_score']
                text_preview = source.get('text', '')[:200] + "..."
                cert_type = source.get('certification_type', 'unknown')
                
                print(f"      {i}. Score: {score:.3f}, Cert: {cert_type}")
                print(f"         Text: {text_preview}")
                print()
                
        except Exception as e:
            print(f"      ❌ AWS Lambda search failed: {str(e)}")
        
        # Test 3: Get embedding for "What is AWS Lambda?" and search
        print("   🔍 Testing vector search for 'What is AWS Lambda?'...")
        try:
            # Generate embedding
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
                print(f"      ✅ Generated embedding: {len(embedding)} dimensions")
                
                # Vector search
                vector_response = client.search(
                    index=index_name,
                    body={
                        "size": 5,
                        "query": {
                            "knn": {
                                "vector_field": {
                                    "vector": embedding,
                                    "k": 5
                                }
                            }
                        }
                    }
                )
                
                vector_hits = vector_response['hits']['hits']
                print(f"      📊 Vector search found {len(vector_hits)} results")
                
                for i, hit in enumerate(vector_hits[:3], 1):
                    source = hit['_source']
                    score = hit['_score']
                    text_preview = source.get('text', '')[:200] + "..."
                    cert_type = source.get('certification_type', 'unknown')
                    
                    print(f"      {i}. Score: {score:.3f}, Cert: {cert_type}")
                    print(f"         Text: {text_preview}")
                    print()
            else:
                print("      ❌ Failed to generate embedding")
                
        except Exception as e:
            print(f"      ❌ Vector search failed: {str(e)}")
        
        # Test 4: Check what certifications are available
        print("   🔍 Checking available certifications...")
        try:
            response = client.search(
                index=index_name,
                body={
                    "size": 0,
                    "aggs": {
                        "certifications": {
                            "terms": {
                                "field": "certification_type",
                                "size": 20
                            }
                        }
                    }
                }
            )
            
            if 'aggregations' in response:
                cert_buckets = response['aggregations']['certifications']['buckets']
                print(f"      📊 Available certifications:")
                for bucket in cert_buckets:
                    cert_type = bucket['key']
                    doc_count = bucket['doc_count']
                    print(f"         - {cert_type}: {doc_count} documents")
            else:
                print("      ⚠️  No aggregation results")
                
        except Exception as e:
            print(f"      ❌ Certification check failed: {str(e)}")
            
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_lambda_search()