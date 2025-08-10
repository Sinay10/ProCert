# index_setup_lambda_src/main.py
import boto3
import json
import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import cfnresponse

def get_opensearch_client(endpoint):
    host = endpoint.replace("https://", "")
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, os.environ['AWS_REGION'], 'aoss')
    return OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_timeout=30
    )

def handler(event, context):
    print(json.dumps(event))
    request_type = event['RequestType']
    props = event['ResourceProperties']
    opensearch_endpoint = props['OpenSearchEndpoint']
    index_name = props['IndexName']
    
    client = get_opensearch_client(opensearch_endpoint)
    
    try:
        if request_type in ['Create', 'Update']:
            index_body = {
                'settings': {
                    'index': {
                        'knn': True,
                        'number_of_shards': 2,
                        'number_of_replicas': 0
                    }
                },
                'mappings': {
                    'properties': {
                        # Vector field for semantic search
                        'vector_field': {
                            'type': 'knn_vector',
                            'dimension': 1536, # Dimension for Titan Embeddings
                            'method': {
                                'name': 'hnsw',
                                'space_type': 'l2',
                                'engine': 'nmslib'
                            }
                        },
                        # Core document fields
                        'document_id': {'type': 'keyword'},
                        'content_id': {'type': 'keyword'},
                        'chunk_index': {'type': 'integer'},
                        'text': {'type': 'text', 'analyzer': 'standard'},
                        
                        # Certification-specific metadata fields
                        'certification_type': {
                            'type': 'keyword',
                            'fields': {
                                'text': {'type': 'text'}
                            }
                        },
                        'certification_level': {'type': 'keyword'},  # foundational, associate, professional, specialty
                        
                        # Content classification fields
                        'content_type': {'type': 'keyword'},
                        'category': {
                            'type': 'keyword',
                            'fields': {
                                'text': {'type': 'text'}
                            }
                        },
                        'subcategory': {'type': 'keyword'},
                        'difficulty_level': {'type': 'keyword'},
                        'tags': {'type': 'keyword'},
                        
                        # Source and processing metadata
                        'source_file': {'type': 'keyword'},
                        'source_bucket': {'type': 'keyword'},
                        'chunk_size': {'type': 'integer'},
                        'processed_at': {'type': 'date'},
                        
                        # Nested metadata object for additional context
                        'metadata': {
                            'type': 'object',
                            'properties': {
                                'extraction_method': {'type': 'keyword'},
                                'question_count': {'type': 'integer'},
                                'total_chunks': {'type': 'integer'},
                                'version': {'type': 'keyword'},
                                'language': {'type': 'keyword'}
                            }
                        }
                    }
                }
            }
            if not client.indices.exists(index=index_name):
                print(f"Creating index '{index_name}'...")
                client.indices.create(index=index_name, body=index_body)
            else:
                print(f"Index '{index_name}' already exists.")

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Data": "Success"})
    except Exception as e:
        print(f"Error: {e}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Data": str(e)})