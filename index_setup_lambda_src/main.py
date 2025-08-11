# index_setup_lambda_src/main.py
import boto3
import json
import os
import urllib3
import cfnresponse
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

def make_opensearch_request(endpoint, method, path, data=None):
    """Make authenticated request to OpenSearch Serverless using boto3"""
    url = f"{endpoint}{path}"
    
    # Create request
    request = AWSRequest(method=method, url=url, data=data, headers={'Content-Type': 'application/json'})
    
    # Sign request
    credentials = boto3.Session().get_credentials()
    SigV4Auth(credentials, 'aoss', os.environ['AWS_REGION']).add_auth(request)
    
    # Make request
    http = urllib3.PoolManager()
    response = http.request(
        method,
        request.url,
        body=request.body,
        headers=dict(request.headers)
    )
    
    return response

def handler(event, context):
    print(json.dumps(event))
    request_type = event['RequestType']
    props = event['ResourceProperties']
    opensearch_endpoint = props['OpenSearchEndpoint']
    index_name = props['IndexName']
    
    try:
        if request_type in ['Create', 'Update']:
            # Check if index exists
            check_response = make_opensearch_request(opensearch_endpoint, 'HEAD', f'/{index_name}')
            
            if check_response.status == 404:  # Index doesn't exist
                print(f"Creating index '{index_name}'...")
                
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
                
                # Create index
                create_response = make_opensearch_request(
                    opensearch_endpoint, 
                    'PUT', 
                    f'/{index_name}',
                    json.dumps(index_body).encode('utf-8')
                )
                
                if create_response.status not in [200, 201]:
                    raise Exception(f"Failed to create index: {create_response.status} - {create_response.data}")
                    
                print(f"Index '{index_name}' created successfully")
            else:
                print(f"Index '{index_name}' already exists")

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Data": "Success"})
    except Exception as e:
        print(f"Error: {e}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Data": str(e)})