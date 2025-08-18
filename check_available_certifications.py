#!/usr/bin/env python3
"""
Check what certification types are available in the OpenSearch index.
"""

import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def check_certifications():
    """Check what certification types have content in OpenSearch."""
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
        
        # Check if index exists
        if not opensearch_client.indices.exists(index=index_name):
            print(f"❌ Index '{index_name}' does not exist")
            return
        
        # Get aggregation of certification types
        agg_query = {
            "size": 0,
            "aggs": {
                "certification_types": {
                    "terms": {
                        "field": "certification_type.keyword",
                        "size": 20
                    }
                },
                "content_types": {
                    "terms": {
                        "field": "content_type.keyword", 
                        "size": 20
                    }
                }
            }
        }
        
        print("🔍 Checking available certification types...")
        response = opensearch_client.search(index=index_name, body=agg_query)
        
        # Print total documents
        total_docs = response['hits']['total']['value']
        print(f"📊 Total documents in index: {total_docs}")
        
        # Print certification types
        cert_buckets = response['aggregations']['certification_types']['buckets']
        if cert_buckets:
            print("\n📋 Available Certification Types:")
            for bucket in cert_buckets:
                cert_type = bucket['key']
                doc_count = bucket['doc_count']
                print(f"  • {cert_type}: {doc_count} documents")
        else:
            print("\n❌ No certification types found")
        
        # Print content types
        content_buckets = response['aggregations']['content_types']['buckets']
        if content_buckets:
            print("\n📄 Available Content Types:")
            for bucket in content_buckets:
                content_type = bucket['key']
                doc_count = bucket['doc_count']
                print(f"  • {content_type}: {doc_count} documents")
        
        # Check for quiz-specific content
        quiz_query = {
            "size": 5,
            "query": {
                "bool": {
                    "should": [
                        {"match": {"content_type": "question"}},
                        {"match": {"content_type": "quiz"}},
                        {"match": {"title": "question"}},
                        {"match": {"content": "question"}}
                    ]
                }
            }
        }
        
        print("\n🎯 Checking for quiz/question content...")
        quiz_response = opensearch_client.search(index=index_name, body=quiz_query)
        quiz_hits = quiz_response['hits']['hits']
        
        if quiz_hits:
            print(f"✅ Found {len(quiz_hits)} potential quiz documents:")
            for hit in quiz_hits:
                source = hit['_source']
                title = source.get('title', 'No title')
                cert_type = source.get('certification_type', 'Unknown')
                content_type = source.get('content_type', 'Unknown')
                print(f"  • {title} ({cert_type}, {content_type})")
        else:
            print("❌ No quiz/question content found")
            print("💡 You may need to upload quiz content to S3 first")
        
        # Sample a few documents to see structure
        print("\n📝 Sample document structure:")
        sample_query = {"size": 1}
        sample_response = opensearch_client.search(index=index_name, body=sample_query)
        
        if sample_response['hits']['hits']:
            sample_doc = sample_response['hits']['hits'][0]['_source']
            print("Sample document keys:", list(sample_doc.keys()))
            if 'certification_type' in sample_doc:
                print(f"Sample certification_type: {sample_doc['certification_type']}")
            if 'content_type' in sample_doc:
                print(f"Sample content_type: {sample_doc['content_type']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Checking Available Certifications in OpenSearch")
    print("=" * 50)
    check_certifications()