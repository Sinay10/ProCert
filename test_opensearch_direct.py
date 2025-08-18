#!/usr/bin/env python3
"""
Test OpenSearch Direct Access

This script tests direct access to the OpenSearch collection to see what's actually there.
"""

import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def test_opensearch_direct():
    """Test direct OpenSearch access."""
    print("🔍 Testing direct OpenSearch access...")
    
    try:
        # Get OpenSearch endpoint from CDK outputs
        with open('cdk-outputs.json', 'r') as f:
            outputs = json.load(f)
        
        stack_outputs = outputs.get("ProcertInfrastructureStack", {})
        opensearch_endpoint = stack_outputs.get('OpenSearchCollectionEndpoint')
        
        if not opensearch_endpoint:
            print("   ❌ OpenSearch endpoint not found")
            return
        
        print(f"   📍 Endpoint: {opensearch_endpoint}")
        
        # Set up client
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
        
        # Test 1: Get cluster info
        print("\n   🔍 Testing cluster info...")
        try:
            info = client.info()
            print(f"      ✅ Cluster name: {info.get('cluster_name', 'unknown')}")
            print(f"      ✅ Version: {info.get('version', {}).get('number', 'unknown')}")
        except Exception as e:
            print(f"      ❌ Cluster info failed: {str(e)}")
        
        # Test 2: List all indices
        print("\n   🔍 Testing index listing...")
        try:
            indices = client.cat.indices(format='json')
            print(f"      📋 Found {len(indices)} indices:")
            for idx in indices:
                print(f"         - {idx.get('index', 'unknown')}: {idx.get('docs.count', '0')} docs")
        except Exception as e:
            print(f"      ❌ Index listing failed: {str(e)}")
        
        # Test 3: Try different index names
        possible_indices = [
            'procert-vector-collection',
            'procert-content',
            'vector-collection',
            'content'
        ]
        
        print("\n   🔍 Testing different index names...")
        for index_name in possible_indices:
            try:
                exists = client.indices.exists(index=index_name)
                print(f"      {'✅' if exists else '❌'} Index '{index_name}': {'exists' if exists else 'not found'}")
                
                if exists:
                    # Get some stats
                    try:
                        stats = client.indices.stats(index=index_name)
                        doc_count = stats['indices'][index_name]['total']['docs']['count']
                        print(f"         📊 Document count: {doc_count}")
                        
                        # Try to get a sample document
                        if doc_count > 0:
                            response = client.search(
                                index=index_name,
                                body={
                                    "size": 1,
                                    "query": {"match_all": {}}
                                }
                            )
                            
                            if response['hits']['hits']:
                                sample_doc = response['hits']['hits'][0]['_source']
                                print(f"         📄 Sample doc keys: {list(sample_doc.keys())}")
                                if 'text' in sample_doc:
                                    print(f"         📝 Text preview: {sample_doc['text'][:100]}...")
                                if 'certification_type' in sample_doc:
                                    print(f"         🎓 Certification: {sample_doc['certification_type']}")
                    except Exception as e:
                        print(f"         ⚠️  Stats failed: {str(e)}")
                        
            except Exception as e:
                print(f"      ❌ Error checking '{index_name}': {str(e)}")
        
        # Test 4: Try a simple search without specifying index
        print("\n   🔍 Testing search without index...")
        try:
            response = client.search(
                body={
                    "size": 1,
                    "query": {"match_all": {}}
                }
            )
            print(f"      ✅ Search successful: {response['hits']['total']['value']} total docs")
        except Exception as e:
            print(f"      ❌ Search failed: {str(e)}")
            
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_opensearch_direct()