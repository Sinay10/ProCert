#!/usr/bin/env python3
"""
Check DynamoDB content metadata table to see what content has been processed.
"""

import boto3
import json
from decimal import Decimal

def decimal_default(obj):
    """JSON serializer for Decimal objects."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def check_content_metadata():
    """Check DynamoDB content metadata table."""
    print("📊 Checking Content Metadata Table...")
    
    dynamodb = boto3.resource('dynamodb')
    
    # Find the content metadata table
    tables = list(dynamodb.tables.all())
    content_table = None
    
    for table in tables:
        if 'content-metadata' in table.name.lower():
            content_table = table
            break
    
    if not content_table:
        print("❌ Content metadata table not found!")
        print("Available tables:")
        for table in tables:
            print(f"   {table.name}")
        return
    
    print(f"Found content metadata table: {content_table.name}")
    
    # Scan the table to see all content
    try:
        response = content_table.scan()
        items = response['Items']
        
        if not items:
            print("\n❌ No content found in metadata table!")
            print("This confirms that the ingestion Lambda hasn't processed any PDFs yet.")
            return
        
        print(f"\n📋 Found {len(items)} content items:")
        
        # Group by certification type
        by_cert_type = {}
        for item in items:
            cert_type = item.get('certification_type', 'UNKNOWN')
            if cert_type not in by_cert_type:
                by_cert_type[cert_type] = []
            by_cert_type[cert_type].append(item)
        
        for cert_type, cert_items in by_cert_type.items():
            print(f"\n   {cert_type} ({len(cert_items)} items):")
            for item in cert_items:
                content_id = item.get('content_id', 'N/A')
                title = item.get('title', 'N/A')
                content_type = item.get('content_type', 'N/A')
                source_file = item.get('source_file', 'N/A')
                question_count = item.get('question_count', 0)
                
                print(f"      {content_id}: {title}")
                print(f"         Type: {content_type}, Questions: {question_count}")
                print(f"         Source: {source_file}")
        
        # Check specifically for ANS content
        ans_items = by_cert_type.get('ANS', [])
        if ans_items:
            print(f"\n✅ Found {len(ans_items)} ANS content items!")
            total_questions = sum(item.get('question_count', 0) for item in ans_items)
            print(f"Total ANS questions available: {total_questions}")
        else:
            print(f"\n❌ No ANS content found in metadata table")
            
    except Exception as e:
        print(f"❌ Error scanning content metadata table: {e}")
    
    # Also check if there are any questions in OpenSearch
    print(f"\n🔍 Checking OpenSearch for ANS questions...")
    try:
        from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
        import os
        
        # Get OpenSearch endpoint from environment or use the known one
        opensearch_endpoint = "https://ju70mw.us-east-1.aoss.amazonaws.com"
        host = opensearch_endpoint.replace("https://", "")
        
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, 'us-east-1', 'aoss')
        
        opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_timeout=30
        )
        
        # Search for ANS questions
        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"certification_type": "ANS"}},
                        {"term": {"content_type": "question"}}
                    ]
                }
            },
            "size": 0  # Just get count
        }
        
        response = opensearch_client.search(
            index="procert-vector-collection",
            body=search_query
        )
        
        total_hits = response['hits']['total']['value']
        print(f"Found {total_hits} ANS questions in OpenSearch")
        
        if total_hits > 0:
            print("✅ ANS questions are available in OpenSearch!")
        else:
            print("❌ No ANS questions found in OpenSearch")
            
    except Exception as e:
        print(f"❌ Error checking OpenSearch: {e}")

if __name__ == "__main__":
    check_content_metadata()