#!/usr/bin/env python3
"""
Analyze Vector Similarity Issues

This script investigates why vector similarity scores are so low and tests different approaches.
"""

import boto3
import json
import numpy as np
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def analyze_vector_similarity():
    """Analyze vector similarity issues."""
    print("🔍 Analyzing Vector Similarity Issues...")
    
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
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Test 1: Check vector magnitudes and normalization
        print("\n   🔍 Test 1: Analyzing stored vectors...")
        
        response = client.search(
            index=index_name,
            body={
                "size": 5,
                "query": {"match_all": {}}
            }
        )
        
        if response['hits']['hits']:
            for i, hit in enumerate(response['hits']['hits'][:3], 1):
                source = hit['_source']
                vector = source.get('vector_field', [])
                
                if vector:
                    vector_np = np.array(vector)
                    magnitude = np.linalg.norm(vector_np)
                    mean_val = np.mean(vector_np)
                    std_val = np.std(vector_np)
                    min_val = np.min(vector_np)
                    max_val = np.max(vector_np)
                    
                    print(f"      Document {i}:")
                    print(f"         Magnitude: {magnitude:.6f}")
                    print(f"         Mean: {mean_val:.6f}")
                    print(f"         Std: {std_val:.6f}")
                    print(f"         Range: [{min_val:.6f}, {max_val:.6f}]")
                    print(f"         Text preview: {source.get('text', '')[:100]}...")
                    print()
        
        # Test 2: Generate query embedding and analyze it
        print("   🔍 Test 2: Analyzing query embedding...")
        
        query_text = "What is AWS Lambda?"
        body = json.dumps({"inputText": query_text})
        
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId="amazon.titan-embed-text-v1",
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        query_embedding = response_body.get("embedding")
        
        if query_embedding:
            query_np = np.array(query_embedding)
            query_magnitude = np.linalg.norm(query_np)
            query_mean = np.mean(query_np)
            query_std = np.std(query_np)
            query_min = np.min(query_np)
            query_max = np.max(query_np)
            
            print(f"      Query embedding:")
            print(f"         Magnitude: {query_magnitude:.6f}")
            print(f"         Mean: {query_mean:.6f}")
            print(f"         Std: {query_std:.6f}")
            print(f"         Range: [{query_min:.6f}, {query_max:.6f}]")
        
        # Test 3: Manual cosine similarity calculation
        print("\n   🔍 Test 3: Manual cosine similarity calculation...")
        
        # Get fresh documents for similarity calculation
        doc_response = client.search(
            index=index_name,
            body={
                "size": 3,
                "query": {"match_all": {}}
            }
        )
        
        if query_embedding and doc_response['hits']['hits']:
            for i, hit in enumerate(doc_response['hits']['hits'][:3], 1):
                source = hit['_source']
                doc_vector = source.get('vector_field', [])
                
                if doc_vector:
                    # Calculate cosine similarity manually
                    query_np = np.array(query_embedding)
                    doc_np = np.array(doc_vector)
                    
                    # Normalize vectors
                    query_norm = query_np / np.linalg.norm(query_np)
                    doc_norm = doc_np / np.linalg.norm(doc_np)
                    
                    # Cosine similarity
                    cosine_sim = np.dot(query_norm, doc_norm)
                    
                    print(f"      Document {i}:")
                    print(f"         Manual cosine similarity: {cosine_sim:.6f}")
                    print(f"         Text: {source.get('text', '')[:100]}...")
                    print()
        
        # Test 4: Test different similarity metrics in OpenSearch
        print("   🔍 Test 4: Testing different OpenSearch similarity metrics...")
        
        if query_embedding:
            # Test with different space_type settings
            similarity_methods = [
                ("l2", "L2 (Euclidean distance)"),
                ("cosinesimil", "Cosine similarity"),
                ("innerproduct", "Inner product")
            ]
            
            for space_type, description in similarity_methods:
                try:
                    print(f"\n      Testing {description}...")
                    
                    # Note: We can't change the index mapping on the fly, but we can try different query approaches
                    vector_response = client.search(
                        index=index_name,
                        body={
                            "size": 3,
                            "query": {
                                "knn": {
                                    "vector_field": {
                                        "vector": query_embedding,
                                        "k": 3
                                    }
                                }
                            }
                        }
                    )
                    
                    vector_hits = vector_response['hits']['hits']
                    if vector_hits:
                        avg_score = sum(hit['_score'] for hit in vector_hits) / len(vector_hits)
                        print(f"         Average score: {avg_score:.6f}")
                        print(f"         Score range: {vector_hits[-1]['_score']:.6f} - {vector_hits[0]['_score']:.6f}")
                    
                except Exception as e:
                    print(f"         ❌ Failed: {str(e)}")
        
        # Test 5: Check if vectors are properly normalized
        print("\n   🔍 Test 5: Vector normalization analysis...")
        
        response = client.search(
            index=index_name,
            body={
                "size": 10,
                "query": {"match_all": {}}
            }
        )
        
        if response['hits']['hits']:
            magnitudes = []
            for hit in response['hits']['hits']:
                vector = hit['_source'].get('vector_field', [])
                if vector:
                    magnitude = np.linalg.norm(np.array(vector))
                    magnitudes.append(magnitude)
            
            if magnitudes:
                print(f"      Vector magnitudes statistics:")
                print(f"         Mean magnitude: {np.mean(magnitudes):.6f}")
                print(f"         Std magnitude: {np.std(magnitudes):.6f}")
                print(f"         Min magnitude: {np.min(magnitudes):.6f}")
                print(f"         Max magnitude: {np.max(magnitudes):.6f}")
                
                # Check if vectors are normalized (magnitude should be ~1.0)
                if np.mean(magnitudes) < 0.5:
                    print(f"      ⚠️  Vectors appear to have very low magnitudes - possible normalization issue")
                elif abs(np.mean(magnitudes) - 1.0) < 0.1:
                    print(f"      ✅ Vectors appear to be normalized (magnitude ~1.0)")
                else:
                    print(f"      ⚠️  Vectors have unusual magnitudes")
        
        # Test 6: Test with more specific Lambda-related content
        print("\n   🔍 Test 6: Testing with Lambda-specific content...")
        
        # First find documents that actually contain "Lambda"
        lambda_docs = client.search(
            index=index_name,
            body={
                "size": 3,
                "query": {
                    "match": {
                        "text": "Lambda"
                    }
                }
            }
        )
        
        if lambda_docs['hits']['hits']:
            print(f"      Found {len(lambda_docs['hits']['hits'])} documents containing 'Lambda'")
            
            # Now test vector similarity with these specific documents
            for i, hit in enumerate(lambda_docs['hits']['hits'], 1):
                source = hit['_source']
                doc_vector = source.get('vector_field', [])
                text_score = hit['_score']  # Text search score
                
                if doc_vector and query_embedding:
                    # Manual cosine similarity
                    query_np = np.array(query_embedding)
                    doc_np = np.array(doc_vector)
                    
                    query_norm = query_np / np.linalg.norm(query_np)
                    doc_norm = doc_np / np.linalg.norm(doc_np)
                    
                    cosine_sim = np.dot(query_norm, doc_norm)
                    
                    print(f"      Document {i} (contains Lambda):")
                    print(f"         Text search score: {text_score:.3f}")
                    print(f"         Vector similarity: {cosine_sim:.6f}")
                    print(f"         Text: {source.get('text', '')[:150]}...")
                    print()
        
    except Exception as e:
        print(f"   ❌ Analysis failed: {str(e)}")

if __name__ == "__main__":
    analyze_vector_similarity()