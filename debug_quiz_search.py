#!/usr/bin/env python3
"""
Debug the quiz search to understand why no questions are found.
"""

import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def debug_quiz_search():
    """Debug the exact search that the quiz Lambda performs."""
    try:
        # Get OpenSearch endpoint from CDK outputs
        with open('cdk-outputs.json', 'r') as f:
            outputs = json.load(f)
        
        stack_outputs = outputs.get("ProcertInfrastructureStack", {})
        opensearch_endpoint = stack_outputs.get('OpenSearchCollectionEndpoint')
        
        if not opensearch_endpoint:
            print("❌ OpenSearch endpoint not found in CDK outputs")
            return
        
        # Set up OpenSearch client
        host = opensearch_endpoint.replace("https://", "")
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, 'us-east-1', 'aoss')
        
        opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20
        )
        
        index_name = "procert-vector-collection"
        
        # Test the exact query that the quiz Lambda uses
        print("🔍 Testing Quiz Lambda Query")
        print("=" * 40)
        
        for cert_type in ['ANS', 'SAA', 'CLF']:
            print(f"\n📋 Testing certification type: {cert_type}")
            
            # This is the exact query from the quiz Lambda
            query = {
                "size": 10,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"content_type": "question"}},
                            {"term": {"certification_type": cert_type}}
                        ]
                    }
                },
                "_source": [
                    "content_id", "text", "certification_type", "category", 
                    "difficulty", "metadata"
                ]
            }
            
            response = opensearch_client.search(body=query, index=index_name)
            hits = response["hits"]["hits"]
            
            print(f"  Results: {len(hits)} documents found")
            
            if hits:
                print("  ✅ Sample document:")
                sample = hits[0]["_source"]
                print(f"    content_id: {sample.get('content_id', 'N/A')}")
                print(f"    certification_type: {sample.get('certification_type', 'N/A')}")
                print(f"    category: {sample.get('category', 'N/A')}")
                print(f"    text preview: {sample.get('text', 'N/A')[:100]}...")
                if 'metadata' in sample:
                    print(f"    metadata keys: {list(sample['metadata'].keys()) if sample['metadata'] else 'None'}")
            else:
                print("  ❌ No documents found")
        
        # Check what content_type values actually exist
        print(f"\n🔍 Checking actual content_type values...")
        content_type_query = {
            "size": 0,
            "aggs": {
                "content_types": {
                    "terms": {
                        "field": "content_type.keyword",
                        "size": 20
                    }
                }
            }
        }
        
        response = opensearch_client.search(body=content_type_query, index=index_name)
        content_buckets = response['aggregations']['content_types']['buckets']
        
        print("Available content_type values:")
        for bucket in content_buckets:
            content_type = bucket['key']
            doc_count = bucket['doc_count']
            print(f"  • {content_type}: {doc_count} documents")
        
        # Try searching with the actual content types
        print(f"\n🔍 Testing with actual content types...")
        for bucket in content_buckets:
            content_type = bucket['key']
            if 'question' in content_type.lower() or 'exam' in content_type.lower():
                print(f"\n📋 Testing content_type: {content_type}")
                
                query = {
                    "size": 5,
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"content_type": content_type}},
                                {"term": {"certification_type": "ANS"}}
                            ]
                        }
                    },
                    "_source": ["content_id", "text", "certification_type", "metadata"]
                }
                
                response = opensearch_client.search(body=query, index=index_name)
                hits = response["hits"]["hits"]
                
                print(f"  Results: {len(hits)} documents found")
                
                if hits:
                    sample = hits[0]["_source"]
                    print(f"    Sample text: {sample.get('text', 'N/A')[:200]}...")
                    if 'metadata' in sample and sample['metadata']:
                        metadata = sample['metadata']
                        print(f"    Metadata keys: {list(metadata.keys())}")
                        if 'question_text' in metadata:
                            print(f"    Has question_text: Yes")
                        if 'answer_options' in metadata:
                            print(f"    Has answer_options: Yes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🐛 Debugging Quiz Search")
    print("=" * 30)
    debug_quiz_search()