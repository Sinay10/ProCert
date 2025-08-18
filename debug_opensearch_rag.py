#!/usr/bin/env python3
"""
Debug OpenSearch RAG System

This script tests if the OpenSearch RAG system is working correctly
by checking the index, searching for content, and testing embeddings.
"""

import os
import json
import boto3
import time
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from botocore.exceptions import ClientError

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

def get_opensearch_client():
    """Get OpenSearch client from environment or CDK outputs."""
    try:
        # Try to get from CDK outputs first
        with open('cdk-outputs.json', 'r') as f:
            outputs = json.load(f)
        
        stack_name = "ProcertInfrastructureStack"
        stack_outputs = outputs.get(stack_name, {})
        
        opensearch_endpoint = stack_outputs.get('OpenSearchCollectionEndpoint')
        opensearch_index = 'procert-vector-collection'  # Correct collection name
        
        if not opensearch_endpoint:
            print("❌ OpenSearch endpoint not found in CDK outputs")
            return None, None
        
        print(f"📍 OpenSearch endpoint: {opensearch_endpoint}")
        print(f"📍 OpenSearch index: {opensearch_index}")
        
        # Set up the OpenSearch client
        host = opensearch_endpoint.replace("https://", "")
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, REGION, 'aoss')
        
        opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_timeout=30
        )
        
        return opensearch_client, opensearch_index
        
    except Exception as e:
        print(f"❌ Error setting up OpenSearch client: {str(e)}")
        return None, None

def test_opensearch_connection(client, index_name):
    """Test basic OpenSearch connection and index status."""
    print("\n🔍 Testing OpenSearch connection...")
    
    try:
        # List all indices using cat API (works better with serverless)
        try:
            indices = client.cat.indices(format='json')
            print(f"   📋 Available indices:")
            doc_count = 0
            for idx in indices:
                idx_name = idx.get('index', 'unknown')
                idx_docs = idx.get('docs.count', '0')
                print(f"      - {idx_name}: {idx_docs} docs")
                if idx_name == index_name:
                    doc_count = int(idx_docs) if idx_docs.isdigit() else 0
        except Exception as e:
            print(f"   ⚠️  Could not list indices: {str(e)}")
        
        # Test if index exists
        if client.indices.exists(index=index_name):
            print(f"   ✅ Index '{index_name}' exists")
            print(f"   📊 Document count: {doc_count}")
            
            return doc_count > 0
        else:
            print(f"   ❌ Index '{index_name}' does not exist")
            return False
            
    except Exception as e:
        print(f"   ❌ OpenSearch connection test failed: {str(e)}")
        return False

def test_bedrock_embeddings():
    """Test Bedrock embedding generation."""
    print("\n🔍 Testing Bedrock embeddings...")
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        
        test_text = "What is AWS Lambda?"
        body = json.dumps({"inputText": test_text})
        
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId="amazon.titan-embed-text-v1",
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        
        if embedding and len(embedding) > 0:
            print(f"   ✅ Embedding generated: {len(embedding)} dimensions")
            print(f"   📊 First 5 values: {embedding[:5]}")
            return embedding
        else:
            print("   ❌ No embedding returned")
            return None
            
    except Exception as e:
        print(f"   ❌ Bedrock embedding test failed: {str(e)}")
        return None

def test_opensearch_search(client, index_name, query_embedding):
    """Test OpenSearch vector search."""
    print("\n🔍 Testing OpenSearch vector search...")
    
    try:
        # Test basic search query
        query = {
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
        
        response = client.search(body=query, index=index_name)
        hits = response.get("hits", {}).get("hits", [])
        
        print(f"   📊 Search results: {len(hits)} documents found")
        
        if hits:
            print("   📄 Top results:")
            for i, hit in enumerate(hits[:3], 1):
                source = hit["_source"]
                score = hit["_score"]
                text_preview = source.get("text", "")[:100] + "..." if len(source.get("text", "")) > 100 else source.get("text", "")
                cert_type = source.get("certification_type", "unknown")
                category = source.get("category", "unknown")
                
                print(f"      {i}. Score: {score:.3f}")
                print(f"         Cert: {cert_type}, Category: {category}")
                print(f"         Text: {text_preview}")
                print()
            
            return True
        else:
            print("   ❌ No search results found")
            return False
            
    except Exception as e:
        print(f"   ❌ OpenSearch search test failed: {str(e)}")
        return False

def test_sample_documents(client, index_name):
    """Test retrieving sample documents from the index."""
    print("\n🔍 Testing sample document retrieval...")
    
    try:
        # Get a few sample documents
        response = client.search(
            index=index_name,
            body={
                "size": 3,
                "query": {"match_all": {}}
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        
        if hits:
            print(f"   📄 Sample documents ({len(hits)}):")
            for i, hit in enumerate(hits, 1):
                source = hit["_source"]
                print(f"      {i}. ID: {source.get('content_id', 'unknown')}")
                print(f"         Cert: {source.get('certification_type', 'unknown')}")
                print(f"         Category: {source.get('category', 'unknown')}")
                print(f"         Text length: {len(source.get('text', ''))}")
                print(f"         Has vector: {'vector_field' in source}")
                print()
            return True
        else:
            print("   ❌ No sample documents found")
            return False
            
    except Exception as e:
        print(f"   ❌ Sample document test failed: {str(e)}")
        return False

def test_rag_pipeline():
    """Test the complete RAG pipeline."""
    print("\n🔍 Testing complete RAG pipeline...")
    
    # Get OpenSearch client
    client, index_name = get_opensearch_client()
    if not client:
        return False
    
    # Test connection
    has_docs = test_opensearch_connection(client, index_name)
    if not has_docs:
        print("   ❌ No documents in index - RAG cannot work")
        return False
    
    # Test sample documents
    test_sample_documents(client, index_name)
    
    # Test embeddings
    embedding = test_bedrock_embeddings()
    if not embedding:
        print("   ❌ Cannot generate embeddings - RAG cannot work")
        return False
    
    # Test search
    search_works = test_opensearch_search(client, index_name, embedding)
    if not search_works:
        print("   ❌ Search not working - RAG cannot work")
        return False
    
    print("   ✅ RAG pipeline appears to be working!")
    return True

def test_chatbot_rag_mode():
    """Test the chatbot in RAG-only mode."""
    print("\n🔍 Testing chatbot RAG-only mode...")
    
    try:
        # Get API endpoint from CDK outputs
        with open('cdk-outputs.json', 'r') as f:
            outputs = json.load(f)
        
        stack_name = "ProcertInfrastructureStack"
        stack_outputs = outputs.get(stack_name, {})
        api_endpoint = stack_outputs.get('ApiEndpoint')
        
        if not api_endpoint:
            print("   ❌ API endpoint not found in CDK outputs")
            return False
        
        print(f"   📍 API endpoint: {api_endpoint}")
        
        # Test RAG-only mode
        import requests
        
        payload = {
            "message": "What is AWS Lambda?",
            "mode": "rag",
            "certification": "aws-solutions-architect-associate"
        }
        
        response = requests.post(
            f"{api_endpoint}/chat/message",
            json=payload,
            timeout=60
        )
        
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            mode_used = result.get('mode_used', 'unknown')
            sources = result.get('sources', [])
            context_quality = result.get('context_quality', {})
            
            print(f"   📝 Response length: {len(response_text)} characters")
            print(f"   🎯 Mode used: {mode_used}")
            print(f"   📚 Sources found: {len(sources)}")
            print(f"   📊 Context quality: {context_quality}")
            
            # Check if it's the fallback message
            if "I don't have enough information" in response_text:
                print("   ❌ RAG mode returned fallback message - not finding relevant content")
                print(f"   💬 Response: {response_text[:200]}...")
                return False
            else:
                print("   ✅ RAG mode returned substantive answer")
                print(f"   💬 Response preview: {response_text[:200]}...")
                return True
        else:
            print(f"   ❌ API request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Chatbot RAG test failed: {str(e)}")
        return False

def main():
    """Run OpenSearch RAG debugging."""
    print("🐛 Debugging OpenSearch RAG System")
    print("=" * 60)
    
    # Test the RAG pipeline components
    pipeline_works = test_rag_pipeline()
    
    if pipeline_works:
        # Test the actual chatbot
        chatbot_works = test_chatbot_rag_mode()
        
        if chatbot_works:
            print("\n✅ RAG system is working correctly!")
        else:
            print("\n❌ RAG pipeline works but chatbot RAG mode is not working")
            print("   This suggests an issue in the chatbot Lambda function")
    else:
        print("\n❌ RAG pipeline has issues - need to fix infrastructure first")
    
    print("\n" + "=" * 60)
    print("🔍 OPENSEARCH RAG DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()