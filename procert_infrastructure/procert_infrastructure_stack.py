# procert_infrastructure/procert_infrastructure_stack.py

from aws_cdk import (
    Stack, RemovalPolicy, CfnOutput, Duration, BundlingOptions, CustomResource,
    aws_s3 as s3, aws_s3_notifications as s3_notifications,
    aws_opensearchserverless as opensearchserverless,
    aws_lambda as lambda_, aws_iam as iam,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    custom_resources as cr
)
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct
import json

class ProcertInfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. INGESTION LAMBDA FUNCTION
        # Check if we're in CI/CD environment to skip Docker bundling
        import os
        skip_bundling = os.environ.get('CI') or os.environ.get('GITLAB_CI')
        
        if skip_bundling:
            # Simple asset bundling for CI/CD (no Docker)
            lambda_code = lambda_.Code.from_asset("lambda_src")
        else:
            # Full Docker bundling for local development and deployment
            lambda_code = lambda_.Code.from_asset("lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=[
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            )
        
        ingestion_lambda = lambda_.Function(self, "ProcertIngestionLambdaV2",
            architecture=lambda_.Architecture.X86_64,
            description="Processes documents from S3 for the ProCert RAG system.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.handler",
            code=lambda_code,
            timeout=Duration.seconds(300),
            memory_size=512
        )

        # 2. CERTIFICATION-AWARE S3 BUCKETS - Complete set for all AWS certifications
        
        # Define all AWS certification types with their bucket configurations
        certification_configs = {
            'general': {'name': 'General', 'description': 'General AWS content and mixed materials'},
            'ccp': {'name': 'CCP', 'description': 'AWS Certified Cloud Practitioner'},
            'aip': {'name': 'AIP', 'description': 'AWS Certified AI Practitioner'},
            'saa': {'name': 'SAA', 'description': 'AWS Certified Solutions Architect Associate'},
            'dva': {'name': 'DVA', 'description': 'AWS Certified Developer Associate'},
            'soa': {'name': 'SOA', 'description': 'AWS Certified SysOps Administrator Associate'},
            'mla': {'name': 'MLA', 'description': 'AWS Certified Machine Learning Engineer Associate'},
            'dea': {'name': 'DEA', 'description': 'AWS Certified Data Engineer Associate'},
            'dop': {'name': 'DOP', 'description': 'AWS Certified DevOps Engineer Professional'},
            'sap': {'name': 'SAP', 'description': 'AWS Certified Solutions Architect Professional'},
            'mls': {'name': 'MLS', 'description': 'AWS Certified Machine Learning Specialty'},
            'scs': {'name': 'SCS', 'description': 'AWS Certified Security Specialty'},
            'ans': {'name': 'ANS', 'description': 'AWS Certified Advanced Networking Specialty'}
        }
        
        # Create buckets for all certifications
        self.certification_buckets = {}
        self.all_materials_buckets = []
        
        for cert_code, config in certification_configs.items():
            bucket = s3.Bucket(self, f"CertificationMaterialsBucket{config['name']}",
                bucket_name=f"procert-materials-{cert_code}-{self.account}",
                versioned=True, 
                encryption=s3.BucketEncryption.S3_MANAGED,
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                removal_policy=RemovalPolicy.RETAIN
            )
            
            # Store bucket reference
            self.certification_buckets[cert_code] = bucket
            self.all_materials_buckets.append(bucket)
            
            # Create output for each bucket
            CfnOutput(self, f"MaterialsBucket{config['name']}Name", 
                     value=bucket.bucket_name,
                     description=f"S3 bucket for {config['description']} materials")

        # Maintain backward compatibility
        self.materials_bucket = self.certification_buckets['general']
        self.materials_bucket_general = self.certification_buckets['general']
        self.materials_bucket_saa = self.certification_buckets['saa']
        self.materials_bucket_dva = self.certification_buckets['dva']
        self.materials_bucket_soa = self.certification_buckets['soa']

        # Apply security policies to all buckets
        for bucket in self.all_materials_buckets:
            bucket.add_to_resource_policy(iam.PolicyStatement(
                effect=iam.Effect.DENY, principals=[iam.AnyPrincipal()], actions=["s3:*"],
                resources=[bucket.arn_for_objects("*")],
                conditions={"Bool": {"aws:SecureTransport": "false"}}
            ))
            bucket.add_to_resource_policy(iam.PolicyStatement(
                effect=iam.Effect.DENY, principals=[iam.AnyPrincipal()], actions=["s3:*"],
                resources=[bucket.arn_for_objects("*")],
                conditions={"NumericLessThan": {"s3:TlsVersion": "1.2"}}
            ))

        # Maintain backward compatibility
        self.materials_bucket = self.materials_bucket_general

        # 3. DYNAMODB TABLES
        # Content metadata table with certification_type as part of partition key
        self.content_metadata_table = dynamodb.Table(self, "ContentMetadataTable",
            table_name=f"procert-content-metadata-{self.account}",
            partition_key=dynamodb.Attribute(
                name="content_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="certification_type",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED
        )

        # Add GSI for querying by certification type and category
        self.content_metadata_table.add_global_secondary_index(
            index_name="CertificationTypeIndex",
            partition_key=dynamodb.Attribute(
                name="certification_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="category",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Add GSI for querying by content type
        self.content_metadata_table.add_global_secondary_index(
            index_name="ContentTypeIndex",
            partition_key=dynamodb.Attribute(
                name="content_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # User progress table with user_id and certification_type as composite key
        self.user_progress_table = dynamodb.Table(self, "UserProgressTable",
            table_name=f"procert-user-progress-{self.account}",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="content_id_certification",  # Format: content_id#certification_type
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED
        )

        # Add GSI for querying user progress by certification type
        self.user_progress_table.add_global_secondary_index(
            index_name="UserCertificationIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="certification_type",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Add GSI for querying progress by timestamp
        self.user_progress_table.add_global_secondary_index(
            index_name="ProgressTimeIndex",
            partition_key=dynamodb.Attribute(
                name="certification_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Conversation context table for chatbot
        self.conversation_table = dynamodb.Table(self, "ConversationTable",
            table_name=f"procert-conversations-{self.account}",
            partition_key=dynamodb.Attribute(
                name="conversation_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl"  # Enable TTL for automatic cleanup
        )

        # Add GSI for querying conversations by user
        self.conversation_table.add_global_secondary_index(
            index_name="UserConversationIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Output table names
        CfnOutput(self, "ContentMetadataTableName", value=self.content_metadata_table.table_name)
        CfnOutput(self, "UserProgressTableName", value=self.user_progress_table.table_name)
        CfnOutput(self, "ConversationTableName", value=self.conversation_table.table_name)
        
        # 5. OPENSEARCH SERVERLESS SETUP
        collection_name = "procert-vector-collection"
        access_policy_document = [{"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"], "Permission": ["aoss:*"]}, {"ResourceType": "index", "Resource": [f"index/{collection_name}/*"], "Permission": ["aoss:*"]}], "Principal": [f"arn:aws:iam::{self.account}:root", ingestion_lambda.role.role_arn, f"arn:aws:iam::{self.account}:user/Admin1"], "Description": "Data access policy for ProCert"}]
        access_policy = opensearchserverless.CfnAccessPolicy(self, "ProcertAccessPolicy", name="procert-access-policy", policy=json.dumps(access_policy_document), type="data")
        
        encryption_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertEncryptionPolicy", name="procert-encryption-policy", type="encryption", policy=json.dumps({"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}], "AWSOwnedKey": True}))
        
        network_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertNetworkPolicy", name="procert-network-policy", type="network", policy=json.dumps([{"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}, {"ResourceType": "dashboard", "Resource": [f"collection/{collection_name}"]}], "AllowFromPublic": True}]))
        
        self.vector_collection = opensearchserverless.CfnCollection(self, "VectorCollection", name=collection_name, type="VECTORSEARCH")
        self.vector_collection.add_dependency(access_policy)
        self.vector_collection.add_dependency(encryption_policy)
        self.vector_collection.add_dependency(network_policy)
        CfnOutput(self, "OpenSearchCollectionEndpoint", value=self.vector_collection.attr_collection_endpoint)

        ingestion_lambda.add_environment("OPENSEARCH_ENDPOINT", self.vector_collection.attr_collection_endpoint)
        ingestion_lambda.add_environment("OPENSEARCH_INDEX", collection_name)
        
        # Add environment variables for DynamoDB tables
        ingestion_lambda.add_environment("CONTENT_METADATA_TABLE", self.content_metadata_table.table_name)
        ingestion_lambda.add_environment("USER_PROGRESS_TABLE", self.user_progress_table.table_name)
        
        # 6. S3 TRIGGERS FOR INGESTION LAMBDA (ALL BUCKETS)
        for bucket in self.all_materials_buckets:
            bucket.add_event_notification(
                s3.EventType.OBJECT_CREATED,
                s3_notifications.LambdaDestination(ingestion_lambda),
                s3.NotificationKeyFilter(suffix=".pdf")
            )

        # 7. PERMISSIONS FOR INGESTION LAMBDA
        # Grant read access to all S3 buckets
        for bucket in self.all_materials_buckets:
            bucket.grant_read(ingestion_lambda)
        
        # Grant DynamoDB permissions
        self.content_metadata_table.grant_read_write_data(ingestion_lambda)
        self.user_progress_table.grant_read_write_data(ingestion_lambda)
        ingestion_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1"]
        ))
        ingestion_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["aoss:APIAccessAll"],
            resources=[self.vector_collection.attr_arn]
        ))

        # --- NEW CHATBOT RESOURCES ---

        # 8. LAMBDA AND CUSTOM RESOURCE TO CREATE THE OPENSEARCH INDEX
        # Index setup lambda with conditional bundling
        if skip_bundling:
            index_lambda_code = lambda_.Code.from_asset("index_setup_lambda_src")
        else:
            index_lambda_code = lambda_.Code.from_asset("index_setup_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=["pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"]
                )
            )
        
        index_setup_lambda = lambda_.Function(self, "ProcertIndexSetupLambda",
            architecture=lambda_.Architecture.X86_64,
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.handler",
            code=index_lambda_code,
            timeout=Duration.seconds(120),
            memory_size=256
        )
        
        index_setup_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["aoss:APIAccessAll"],
            resources=[self.vector_collection.attr_arn]
        ))
        
        provider = cr.Provider(self, "ProcertIndexSetupProvider",
            on_event_handler=index_setup_lambda,
            log_retention=RetentionDays.ONE_DAY
        )

        CustomResource(self, "ProcertIndexSetupResource",
            service_token=provider.service_token,
            properties={
                "OpenSearchEndpoint": self.vector_collection.attr_collection_endpoint,
                "IndexName": collection_name
            }
        )
        # 9. CHATBOT LAMBDA FUNCTION
        # Chatbot lambda with conditional bundling
        if skip_bundling:
            chatbot_lambda_code = lambda_.Code.from_asset("chatbot_lambda_src")
        else:
            chatbot_lambda_code = lambda_.Code.from_asset("chatbot_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=[
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            )
        
        chatbot_lambda = lambda_.Function(self, "ProcertChatbotLambda",
            architecture=lambda_.Architecture.X86_64,
            description="Handles user queries for the ProCert RAG system with dual-mode responses.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.handler",
            code=chatbot_lambda_code,
            timeout=Duration.seconds(60),  # Increased timeout for enhanced mode
            memory_size=1024,  # Increased memory for conversation management
            environment={
                "OPENSEARCH_ENDPOINT": self.vector_collection.attr_collection_endpoint,
                "OPENSEARCH_INDEX": collection_name,
                "CONTENT_METADATA_TABLE": self.content_metadata_table.table_name,
                "USER_PROGRESS_TABLE": self.user_progress_table.table_name,
                "CONVERSATION_TABLE": self.conversation_table.table_name
            }
        )

        # 10. PERMISSIONS FOR CHATBOT LAMBDA
        chatbot_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["aoss:APIAccessAll"],
            resources=[self.vector_collection.attr_arn]
        ))
        
        chatbot_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1",
                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
            ]
        ))

        # Grant DynamoDB permissions to chatbot lambda
        self.content_metadata_table.grant_read_write_data(chatbot_lambda)
        self.user_progress_table.grant_read_write_data(chatbot_lambda)
        self.conversation_table.grant_read_write_data(chatbot_lambda)

        # Grant read access to all S3 buckets for chatbot lambda (for content retrieval)
        for bucket in self.all_materials_buckets:
            bucket.grant_read(chatbot_lambda)

        # 11. API GATEWAY
        api = apigateway.RestApi(self, "ProcertApi",
            rest_api_name="ProCert Service",
            description="This service handles ProCert queries and conversations.",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )

        # Chat endpoints
        chat_integration = apigateway.LambdaIntegration(chatbot_lambda)
        chat_resource = api.root.add_resource("chat")
        
        # POST /chat/message - Send message
        message_resource = chat_resource.add_resource("message")
        message_resource.add_method("POST", chat_integration)
        
        # GET /chat/conversation/{id} - Get conversation
        conversation_resource = chat_resource.add_resource("conversation")
        conversation_id_resource = conversation_resource.add_resource("{id}")
        conversation_id_resource.add_method("GET", chat_integration)
        
        # DELETE /chat/conversation/{id} - Delete conversation
        conversation_id_resource.add_method("DELETE", chat_integration)

        # Maintain backward compatibility
        query_resource = api.root.add_resource("query")
        query_resource.add_method("POST", chat_integration)

        CfnOutput(self, "ApiEndpoint", value=api.url)