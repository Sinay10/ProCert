"""
JWT Authorizer Lambda Function for API Gateway.

Validates JWT tokens from AWS Cognito and returns IAM policies
for API Gateway authorization.
"""

import os
import sys
import json
import logging

# Add shared directory to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from jwt_middleware import lambda_authorizer_handler

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda authorizer handler.
    
    This function is called by API Gateway to validate JWT tokens
    and return IAM policies for authorization.
    """
    return lambda_authorizer_handler(event, context)