# lambda_src/main.py

import os
import json
import boto3
from urllib.parse import unquote_plus

# Placeholder for text extraction logic
def extract_text(bucket, key):
    """Extracts text from a file in S3."""
    print(f"Extracting text from {bucket}/{key}")
    # TODO: Add logic to download file and extract text based on file type (.pdf, .docx)
    return "This is a sample text from the document."

# Placeholder for text chunking logic
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """Splits text into smaller chunks."""
    print("Chunking text...")
    # TODO: Implement a more sophisticated chunking strategy
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]

# Placeholder for Bedrock embedding generation
def get_embeddings(chunks):
    """Generates embeddings for a list of text chunks."""
    print(f"Generating embeddings for {len(chunks)} chunks...")
    # TODO: Call the Bedrock API to get embeddings for each chunk
    return [[0.1, 0.2, 0.3] for _ in chunks] # Return dummy embeddings

# Placeholder for OpenSearch storage logic
def store_embeddings(chunks, embeddings):
    """Stores text chunks and their embeddings in OpenSearch."""
    print(f"Storing {len(chunks)} documents in OpenSearch...")
    # TODO: Use the opensearch-py client to index the documents
    return True


def handler(event, context):
    """
    Main Lambda handler for the data ingestion pipeline.
    Triggered by an S3 object creation event.
    """
    s3_client = boto3.client('s3')
    
    # 1. Get the uploaded file's information from the S3 event
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = unquote_plus(record['s3']['object']['key'])
    
    print(f"Processing new file: s3://{bucket}/{key}")

    try:
        # 2. Extract text from the document
        document_text = extract_text(bucket, key)
        
        # 3. Split the text into manageable chunks
        text_chunks = chunk_text(document_text)
        
        # 4. Generate vector embeddings for each chunk using Amazon Bedrock
        chunk_embeddings = get_embeddings(text_chunks)
        
        # 5. Store the chunks and their embeddings in OpenSearch
        success = store_embeddings(text_chunks, chunk_embeddings)

        if success:
            print("Successfully processed and stored the document.")
            return {'statusCode': 200, 'body': json.dumps('Document processed successfully!')}
        else:
            raise Exception("Failed to store embeddings.")

    except Exception as e:
        print(f"Error processing file {key}: {e}")
        # Consider adding error notification logic here (e.g., to an SNS topic)
        return {'statusCode': 500, 'body': json.dumps(f'Error: {e}')}