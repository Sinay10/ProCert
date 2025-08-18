#!/usr/bin/env python3
"""
Debug the question metadata to see what's missing.
"""

import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def debug_question_metadata():
    """Debug the question metadata structure."""
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
        
        # Get a few sample questions to examine their metadata
        query = {
            "size": 3,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"content_type": "question"}},
                        {"term": {"certification_type": "ANS"}}
                    ]
                }
            }
        }
        
        response = opensearch_client.search(body=query, index=index_name)
        hits = response["hits"]["hits"]
        
        print(f"🔍 Examining {len(hits)} question documents")
        print("=" * 50)
        
        for i, hit in enumerate(hits):
            source = hit["_source"]
            print(f"\n📋 Question {i+1}:")
            print(f"  content_id: {source.get('content_id')}")
            print(f"  certification_type: {source.get('certification_type')}")
            print(f"  category: {source.get('category')}")
            
            metadata = source.get("metadata", {})
            if metadata:
                print(f"  📊 Metadata structure:")
                for key, value in metadata.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"    {key}: {value[:100]}... (truncated)")
                    else:
                        print(f"    {key}: {value}")
                
                # Check required fields for quiz
                required_fields = ['question_text', 'answer_options', 'correct_answer']
                missing_fields = [field for field in required_fields if field not in metadata]
                
                if missing_fields:
                    print(f"  ❌ Missing required fields: {missing_fields}")
                else:
                    print(f"  ✅ All required fields present")
                    
                    # Validate answer_options format
                    answer_options = metadata.get('answer_options')
                    if isinstance(answer_options, list):
                        print(f"  ✅ answer_options is a list with {len(answer_options)} options")
                        for j, option in enumerate(answer_options):
                            print(f"    {chr(65+j)}) {option}")
                    else:
                        print(f"  ⚠️  answer_options format: {type(answer_options)} - {answer_options}")
                    
                    # Check correct_answer format
                    correct_answer = metadata.get('correct_answer')
                    print(f"  ✅ correct_answer: {correct_answer}")
            else:
                print(f"  ❌ No metadata found")
            
            # Show a bit of the text content
            text = source.get('text', '')
            if text:
                print(f"  📄 Text preview: {text[:200]}...")
        
        # Test the exact logic from the quiz Lambda
        print(f"\n🧪 Testing Quiz Lambda Logic")
        print("=" * 35)
        
        questions = []
        for hit in hits:
            source = hit["_source"]
            metadata = source.get("metadata", {})
            
            if metadata and "question_text" in metadata and "answer_options" in metadata:
                print(f"✅ Processing question with metadata")
                question_data = {
                    "question_text": metadata["question_text"],
                    "answer_options": metadata["answer_options"],
                    "correct_answer": metadata.get("correct_answer", "A"),
                    "question_type": metadata.get("question_type", "multiple_choice"),
                    "content_id": source.get("content_id"),
                    "certification_type": source.get("certification_type"),
                    "category": source.get("category", "general"),
                    "difficulty": source.get("difficulty", "intermediate")
                }
                questions.append(question_data)
                print(f"  Added question: {question_data['content_id']}")
            else:
                print(f"❌ Skipping question - missing metadata fields")
        
        print(f"\n📊 Final Results:")
        print(f"  Total questions processed: {len(questions)}")
        
        if questions:
            print(f"  ✅ Quiz generation should work!")
            sample_question = questions[0]
            print(f"  Sample question structure:")
            for key, value in sample_question.items():
                if isinstance(value, str) and len(value) > 50:
                    print(f"    {key}: {value[:50]}...")
                else:
                    print(f"    {key}: {value}")
        else:
            print(f"  ❌ No valid questions found - quiz generation will fail")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_question_metadata()