#!/usr/bin/env python3
"""
Trigger Ingestion and Test RAG System

This script triggers the ingestion Lambda for all PDF files in S3,
waits for processing, then tests the RAG system.
"""

import boto3
import json
import time
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

def get_opensearch_client():
    """Get OpenSearch client from CDK outputs."""
    try:
        with open('cdk-outputs.json', 'r') as f:
            outputs = json.load(f)
        
        stack_outputs = outputs.get("ProcertInfrastructureStack", {})
        opensearch_endpoint = stack_outputs.get('OpenSearchCollectionEndpoint')
        
        if not opensearch_endpoint:
            print("❌ OpenSearch endpoint not found")
            return None, None
        
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
        
        return opensearch_client, 'procert-content'
        
    except Exception as e:
        print(f"❌ Error setting up OpenSearch client: {str(e)}")
        return None, None

def find_ingestion_lambda():
    """Find the correct ingestion Lambda function name."""
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        response = lambda_client.list_functions()
        functions = response['Functions']
        
        # Look for ingestion lambda
        for func in functions:
            if 'IngestionLambda' in func['FunctionName'] and 'V2' in func['FunctionName']:
                return func['FunctionName']
        
        return None
    except Exception as e:
        print(f"❌ Error finding Lambda: {str(e)}")
        return None

def trigger_ingestion_for_bucket(bucket_name, lambda_name):
    """Trigger ingestion for all PDF files in a bucket."""
    print(f"\n🚀 Triggering ingestion for bucket: {bucket_name}")
    
    s3_client = boto3.client('s3', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        # List PDF files in bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' not in response:
            print(f"   📁 No files found in {bucket_name}")
            return 0
        
        pdf_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.pdf')]
        print(f"   📄 Found {len(pdf_files)} PDF files")
        
        processed = 0
        for pdf_file in pdf_files:
            file_key = pdf_file['Key']
            print(f"   📤 Processing: {file_key}")
            
            # Create S3 event payload
            event_payload = {
                "Records": [
                    {
                        "eventVersion": "2.1",
                        "eventSource": "aws:s3",
                        "eventName": "ObjectCreated:Put",
                        "s3": {
                            "bucket": {"name": bucket_name},
                            "object": {"key": file_key}
                        }
                    }
                ]
            }
            
            try:
                response = lambda_client.invoke(
                    FunctionName=lambda_name,
                    InvocationType='Event',  # Async invocation
                    Payload=json.dumps(event_payload)
                )
                
                if response['StatusCode'] == 202:
                    print(f"      ✅ Triggered ingestion for {file_key}")
                    processed += 1
                else:
                    print(f"      ❌ Failed to trigger ingestion for {file_key}")
                    
            except Exception as e:
                print(f"      ❌ Error triggering {file_key}: {str(e)}")
        
        return processed
        
    except Exception as e:
        print(f"   ❌ Error processing bucket {bucket_name}: {str(e)}")
        return 0

def wait_for_ingestion(client, index_name, expected_docs=0, max_wait=300):
    """Wait for ingestion to complete."""
    print(f"\n⏳ Waiting for ingestion to complete (max {max_wait}s)...")
    
    start_time = time.time()
    last_count = 0
    
    while time.time() - start_time < max_wait:
        try:
            if client.indices.exists(index=index_name):
                stats = client.indices.stats(index=index_name)
                doc_count = stats['indices'][index_name]['total']['docs']['count']
                
                if doc_count != last_count:
                    print(f"   📊 Current document count: {doc_count}")
                    last_count = doc_count
                
                if doc_count > 0 and (expected_docs == 0 or doc_count >= expected_docs):
                    print(f"   ✅ Ingestion complete! {doc_count} documents indexed")
                    return True
            else:
                print(f"   ⏳ Index '{index_name}' not yet created...")
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"   ⚠️  Error checking ingestion status: {str(e)}")
            time.sleep(10)
    
    print(f"   ⏰ Timeout waiting for ingestion after {max_wait}s")
    return False

def test_rag_after_ingestion(client, index_name):
    """Test RAG functionality after ingestion."""
    print(f"\n🧪 Testing RAG functionality...")
    
    try:
        # Test 1: Check document count
        stats = client.indices.stats(index=index_name)
        doc_count = stats['indices'][index_name]['total']['docs']['count']
        print(f"   📊 Total documents: {doc_count}")
        
        # Test 2: Sample a few documents
        response = client.search(
            index=index_name,
            body={
                "size": 3,
                "query": {"match_all": {}}
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        print(f"   📄 Sample documents:")
        for i, hit in enumerate(hits, 1):
            source = hit["_source"]
            text_preview = source.get("text", "")[:100] + "..." if len(source.get("text", "")) > 100 else source.get("text", "")
            print(f"      {i}. Cert: {source.get('certification_type', 'unknown')}")
            print(f"         Category: {source.get('category', 'unknown')}")
            print(f"         Text: {text_preview}")
            print()
        
        # Test 3: Test embedding search
        print("   🔍 Testing embedding search...")
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
        
        if embedding:
            # Search with embedding
            query = {
                "size": 3,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "vector_field": {
                                        "vector": embedding,
                                        "k": 3
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            search_response = client.search(body=query, index=index_name)
            search_hits = search_response.get("hits", {}).get("hits", [])
            
            print(f"      📊 Vector search results: {len(search_hits)} documents")
            for i, hit in enumerate(search_hits, 1):
                source = hit["_source"]
                score = hit["_score"]
                text_preview = source.get("text", "")[:100] + "..." if len(source.get("text", "")) > 100 else source.get("text", "")
                print(f"         {i}. Score: {score:.3f}")
                print(f"            Text: {text_preview}")
            
            if search_hits:
                print("   ✅ Vector search working!")
                return True
            else:
                print("   ❌ Vector search returned no results")
                return False
        else:
            print("   ❌ Could not generate embedding for search")
            return False
            
    except Exception as e:
        print(f"   ❌ RAG test failed: {str(e)}")
        return False

def main():
    """Main function to trigger ingestion and test RAG."""
    print("🚀 Triggering Ingestion and Testing RAG System")
    print("=" * 60)
    
    # Find ingestion Lambda
    lambda_name = find_ingestion_lambda()
    if not lambda_name:
        print("❌ Could not find ingestion Lambda function")
        return
    
    print(f"📍 Using Lambda: {lambda_name}")
    
    # Get OpenSearch client
    client, index_name = get_opensearch_client()
    if not client:
        print("❌ Could not connect to OpenSearch")
        return
    
    print(f"📍 Using OpenSearch index: {index_name}")
    
    # Trigger ingestion for SAA bucket (main one with content)
    saa_bucket = f"procert-materials-saa-{ACCOUNT_ID}"
    processed = trigger_ingestion_for_bucket(saa_bucket, lambda_name)
    
    if processed > 0:
        print(f"\n✅ Triggered ingestion for {processed} files")
        
        # Wait for ingestion to complete
        if wait_for_ingestion(client, index_name, max_wait=600):  # 10 minutes max
            # Test RAG functionality
            if test_rag_after_ingestion(client, index_name):
                print("\n🎉 RAG system is now working!")
                
                # Test the chatbot
                print("\n🤖 Testing chatbot RAG mode...")
                import requests
                
                with open('cdk-outputs.json', 'r') as f:
                    outputs = json.load(f)
                
                stack_outputs = outputs.get("ProcertInfrastructureStack", {})
                api_endpoint = stack_outputs.get('ApiEndpoint')
                
                if api_endpoint:
                    payload = {
                        "message": "What is AWS Lambda?",
                        "mode": "rag",
                        "certification": "aws-solutions-architect-associate"
                    }
                    
                    try:
                        response = requests.post(
                            f"{api_endpoint}/chat/message",
                            json=payload,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            response_text = result.get('response', '')
                            mode_used = result.get('mode_used', 'unknown')
                            sources = result.get('sources', [])
                            
                            print(f"   📝 Response mode: {mode_used}")
                            print(f"   📚 Sources: {len(sources)}")
                            
                            if "I don't have enough information" in response_text:
                                print("   ❌ Still getting fallback message")
                                print(f"   💬 Response: {response_text[:200]}...")
                            else:
                                print("   ✅ RAG mode working in chatbot!")
                                print(f"   💬 Response: {response_text[:200]}...")
                        else:
                            print(f"   ❌ Chatbot test failed: {response.status_code}")
                    except Exception as e:
                        print(f"   ❌ Chatbot test error: {str(e)}")
                else:
                    print("   ⚠️  Could not find API endpoint for chatbot test")
            else:
                print("\n❌ RAG system still not working after ingestion")
        else:
            print("\n❌ Ingestion did not complete in time")
    else:
        print("\n❌ No files were processed for ingestion")
    
    print("\n" + "=" * 60)
    print("🔍 INGESTION AND RAG TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()