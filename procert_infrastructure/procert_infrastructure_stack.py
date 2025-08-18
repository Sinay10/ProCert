# procert_infrastructure/procert_infrastructure_stack.py

from aws_cdk import (
    Stack, RemovalPolicy, CfnOutput, Duration, BundlingOptions, CustomResource,
    aws_s3 as s3, aws_s3_notifications as s3_notifications,
    aws_opensearchserverless as opensearchserverless,
    aws_lambda as lambda_, aws_iam as iam,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    custom_resources as cr
)
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct
import json

class ProcertInfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 0. VPC SETUP FOR SECURE OPENSEARCH ACCESS
        # Create VPC with private subnets for Lambda functions
        self.vpc = ec2.Vpc(self, "ProcertVpc",
            vpc_name=f"procert-vpc-{self.account}",
            max_azs=2,  # Use 2 AZs for high availability
            nat_gateways=1,  # Single NAT gateway for cost optimization
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Public", 
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # Security group for Lambda functions accessing OpenSearch
        self.lambda_security_group = ec2.SecurityGroup(self, "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions accessing OpenSearch Serverless",
            allow_all_outbound=True
        )

        # Note: VPC Endpoint for OpenSearch Serverless not available in us-east-1
        # Using public access which works perfectly for our use case
        
        # Output VPC details
        CfnOutput(self, "VpcId", value=self.vpc.vpc_id)

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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
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

        # User profiles table for authentication and profile management
        self.user_profiles_table = dynamodb.Table(self, "UserProfilesTable",
            table_name=f"procert-user-profiles-{self.account}",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            encryption=dynamodb.TableEncryption.AWS_MANAGED
        )

        # Add GSI for querying by email
        self.user_profiles_table.add_global_secondary_index(
            index_name="EmailIndex",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Quiz sessions table for quiz management
        self.quiz_sessions_table = dynamodb.Table(self, "QuizSessionsTable",
            table_name=f"procert-quiz-sessions-{self.account}",
            partition_key=dynamodb.Attribute(
                name="quiz_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            encryption=dynamodb.TableEncryption.AWS_MANAGED
        )

        # Add GSI for querying user's quiz sessions
        self.quiz_sessions_table.add_global_secondary_index(
            index_name="UserQuizIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="started_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Study recommendations table
        self.recommendations_table = dynamodb.Table(self, "RecommendationsTable",
            table_name=f"procert-recommendations-{self.account}",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="recommendation_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="expires_at"  # Enable TTL for automatic cleanup
        )

        # Output table names
        CfnOutput(self, "ContentMetadataTableName", value=self.content_metadata_table.table_name)
        CfnOutput(self, "UserProgressTableName", value=self.user_progress_table.table_name)
        CfnOutput(self, "ConversationTableName", value=self.conversation_table.table_name)
        CfnOutput(self, "UserProfilesTableName", value=self.user_profiles_table.table_name)
        CfnOutput(self, "QuizSessionsTableName", value=self.quiz_sessions_table.table_name)
        CfnOutput(self, "RecommendationsTableName", value=self.recommendations_table.table_name)
        
        # 4. COGNITO USER POOL AND IDENTITY POOL
        # User Pool for authentication
        self.user_pool = cognito.UserPool(self, "ProcertUserPool",
            user_pool_name=f"procert-users-{self.account}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN,
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=True, mutable=True),
                family_name=cognito.StandardAttribute(required=True, mutable=True)
            ),
            custom_attributes={
                "target_certs": cognito.StringAttribute(mutable=True),
                "study_prefs": cognito.StringAttribute(mutable=True)
            }
        )

        # User Pool Client for web application
        self.user_pool_client = cognito.UserPoolClient(self, "ProcertUserPoolClient",
            user_pool=self.user_pool,
            user_pool_client_name=f"procert-web-client-{self.account}",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True
            ),
            generate_secret=False,  # For web clients, no secret needed
            prevent_user_existence_errors=True,
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30)
        )

        # Identity Pool for AWS resource access
        self.identity_pool = cognito.CfnIdentityPool(self, "ProcertIdentityPool",
            identity_pool_name=f"procert_identity_pool_{self.account}",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name
                )
            ]
        )

        # IAM roles for authenticated users
        authenticated_role = iam.Role(self, "CognitoAuthenticatedRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            ),
            inline_policies={
                "CognitoAuthenticatedPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "cognito-sync:*",
                                "cognito-identity:*"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Attach the roles to the identity pool
        cognito.CfnIdentityPoolRoleAttachment(self, "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={
                "authenticated": authenticated_role.role_arn
            }
        )

        # Output Cognito details
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
        CfnOutput(self, "IdentityPoolId", value=self.identity_pool.ref)
        
        # 5. OPENSEARCH SERVERLESS SETUP
        collection_name = "procert-vector-collection"
        
        # Restrict OpenSearch permissions to only what's needed (principle of least privilege)
        # Access policy will be created after all Lambda functions are defined
        # For now, create a placeholder that will be replaced
        access_policy = None
        
        encryption_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertEncryptionPolicy", name="procert-encryption-policy", type="encryption", policy=json.dumps({"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}], "AWSOwnedKey": True}))
        
        # Network policy - Allow public access (VPC endpoint not available in all regions)
        network_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertNetworkPolicy", 
            name="procert-network-policy", 
            type="network", 
            policy=json.dumps([{
                "Rules": [
                    {"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}, 
                    {"ResourceType": "dashboard", "Resource": [f"collection/{collection_name}"]}
                ], 
                "AllowFromPublic": True
            }])
        )
        
        self.vector_collection = opensearchserverless.CfnCollection(self, "VectorCollection", name=collection_name, type="VECTORSEARCH")
        # Vector collection dependency will be added after access policy is created
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
        # Grant specific OpenSearch permissions (principle of least privilege)
        ingestion_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "aoss:ReadDocument",
                "aoss:WriteDocument", 
                "aoss:CreateIndex",
                "aoss:DescribeIndex"
            ],
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
        
        # Grant specific OpenSearch permissions for index setup
        index_setup_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "aoss:CreateIndex",
                "aoss:DescribeIndex",
                "aoss:UpdateIndex"
            ],
            resources=[self.vector_collection.attr_arn]
        ))
        
        # Create log group for the custom resource provider
        from aws_cdk import aws_logs as logs
        provider_log_group = logs.LogGroup(self, "ProcertIndexSetupProviderLogGroup",
            log_group_name=f"/aws/lambda/ProcertInfrastructureStack-ProcertIndexSetupProvider",
            retention=RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        provider = cr.Provider(self, "ProcertIndexSetupProvider",
            on_event_handler=index_setup_lambda,
            log_group=provider_log_group
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
            timeout=Duration.seconds(25),  # Reduced to stay under API Gateway 30s limit
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
        # Grant specific OpenSearch permissions for search operations
        chatbot_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "aoss:ReadDocument",
                "aoss:DescribeIndex"
            ],
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

        # 10.5. USER PROFILE MANAGEMENT LAMBDA
        # User profile lambda with conditional bundling
        if skip_bundling:
            user_profile_lambda_code = lambda_.Code.from_asset("user_profile_lambda_src")
        else:
            user_profile_lambda_code = lambda_.Code.from_asset("user_profile_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=[
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            )
        
        user_profile_lambda = lambda_.Function(self, "ProcertUserProfileLambda",
            architecture=lambda_.Architecture.X86_64,
            description="Handles user authentication and profile management for the ProCert Learning Platform.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.lambda_handler",
            code=user_profile_lambda_code,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "USER_PROFILES_TABLE": self.user_profiles_table.table_name,
                "USER_POOL_ID": self.user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": self.user_pool_client.user_pool_client_id,
                "QUIZ_SESSIONS_TABLE": self.quiz_sessions_table.table_name,
                "RECOMMENDATIONS_TABLE": self.recommendations_table.table_name
            }
        )

        # Grant DynamoDB permissions to user profile lambda
        self.user_profiles_table.grant_read_write_data(user_profile_lambda)
        self.quiz_sessions_table.grant_read_write_data(user_profile_lambda)
        self.recommendations_table.grant_read_write_data(user_profile_lambda)

        # Grant Cognito permissions to user profile lambda
        user_profile_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminSetUserPassword",
                "cognito-idp:AdminInitiateAuth",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:GetUser",
                "cognito-idp:ForgotPassword",
                "cognito-idp:ConfirmForgotPassword"
            ],
            resources=[self.user_pool.user_pool_arn]
        ))

        # 10.5.5. QUIZ GENERATION SERVICE LAMBDA
        # Quiz lambda with conditional bundling
        if skip_bundling:
            quiz_lambda_code = lambda_.Code.from_asset("quiz_lambda_src")
        else:
            quiz_lambda_code = lambda_.Code.from_asset("quiz_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=[
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            )
        
        quiz_lambda = lambda_.Function(self, "ProcertQuizLambda",
            architecture=lambda_.Architecture.X86_64,
            description="Handles quiz generation, session management, and scoring for the ProCert Learning Platform.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.lambda_handler",
            code=quiz_lambda_code,
            timeout=Duration.seconds(30),
            memory_size=1024,
            environment={
                "QUIZ_SESSIONS_TABLE": self.quiz_sessions_table.table_name,
                "USER_PROGRESS_TABLE": self.user_progress_table.table_name,
                "CONTENT_METADATA_TABLE": self.content_metadata_table.table_name,
                "OPENSEARCH_ENDPOINT": self.vector_collection.attr_collection_endpoint,
                "OPENSEARCH_INDEX": collection_name,
                "OPENSEARCH_REGION": self.region
            }
        )

        # Grant DynamoDB permissions to quiz lambda
        self.quiz_sessions_table.grant_read_write_data(quiz_lambda)
        self.user_progress_table.grant_read_write_data(quiz_lambda)
        self.content_metadata_table.grant_read_data(quiz_lambda)

        # Grant specific OpenSearch permissions to quiz lambda
        quiz_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "aoss:ReadDocument",
                "aoss:DescribeIndex"
            ],
            resources=[self.vector_collection.attr_arn]
        ))

        # Grant Bedrock permissions to quiz lambda (for potential AI-powered features)
        quiz_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1",
                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
            ]
        ))

        # 10.6. ENHANCED PROGRESS TRACKING LAMBDA
        # Progress tracking lambda with conditional bundling
        if skip_bundling:
            progress_lambda_code = lambda_.Code.from_asset("progress_lambda_src")
        else:
            progress_lambda_code = lambda_.Code.from_asset("progress_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=[
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            )
        
        progress_lambda = lambda_.Function(self, "ProcertProgressLambda",
            architecture=lambda_.Architecture.X86_64,
            description="Enhanced progress tracking and analytics for the ProCert Learning Platform.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.lambda_handler",
            code=progress_lambda_code,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "USER_PROGRESS_TABLE_NAME": self.user_progress_table.table_name,
                "CONTENT_METADATA_TABLE_NAME": self.content_metadata_table.table_name
            }
        )

        # Grant DynamoDB permissions to progress lambda
        self.user_progress_table.grant_read_write_data(progress_lambda)
        self.content_metadata_table.grant_read_data(progress_lambda)

        # 10.7. JWT AUTHORIZER LAMBDA
        # JWT authorizer lambda with conditional bundling
        if skip_bundling:
            jwt_authorizer_lambda_code = lambda_.Code.from_asset("jwt_authorizer_lambda_src")
        else:
            jwt_authorizer_lambda_code = lambda_.Code.from_asset("jwt_authorizer_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=[
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            )
        
        jwt_authorizer_lambda = lambda_.Function(self, "ProcertJWTAuthorizerLambda",
            architecture=lambda_.Architecture.X86_64,
            description="JWT token validation authorizer for the ProCert Learning Platform API.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.lambda_handler",
            code=jwt_authorizer_lambda_code,
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={
                "USER_POOL_ID": self.user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": self.user_pool_client.user_pool_client_id
            }
        )

        # 10.6. RECOMMENDATION ENGINE LAMBDA
        # Recommendation lambda with conditional bundling
        if skip_bundling:
            recommendation_lambda_code = lambda_.Code.from_asset("recommendation_lambda_src")
        else:
            recommendation_lambda_code = lambda_.Code.from_asset("recommendation_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=[
                        "pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            )
        
        # ML Layer for advanced recommendation algorithms
        # Make layer ARN configurable instead of hardcoded for better portability
        ml_layer_arn = self.node.try_get_context("ml_layer_arn")
        if not ml_layer_arn:
            # Default to current layer but make it account/region aware
            ml_layer_arn = f"arn:aws:lambda:{self.region}:{self.account}:layer:procert-ml-dependencies:1"
        
        ml_layer = lambda_.LayerVersion.from_layer_version_arn(
            self, 'MLLayer', 
            ml_layer_arn
        )
        
        recommendation_lambda = lambda_.Function(self, "ProcertRecommendationLambda",
            architecture=lambda_.Architecture.X86_64,
            description="Provides ML-based personalized study recommendations for the ProCert Learning Platform.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.lambda_handler",
            code=recommendation_lambda_code,
            timeout=Duration.seconds(30),
            memory_size=1024,
            layers=[ml_layer],
            environment={
                "USER_PROGRESS_TABLE_NAME": self.user_progress_table.table_name,
                "CONTENT_METADATA_TABLE_NAME": self.content_metadata_table.table_name,
                "RECOMMENDATIONS_TABLE_NAME": self.recommendations_table.table_name
            }
        )

        # Grant DynamoDB permissions to recommendation lambda
        self.user_progress_table.grant_read_data(recommendation_lambda)
        self.content_metadata_table.grant_read_data(recommendation_lambda)
        self.recommendations_table.grant_read_write_data(recommendation_lambda)

        # 10.8. OPENSEARCH ACCESS POLICY (after all Lambda functions are created)
        # Updated policy to ensure quiz Lambda has proper access
        access_policy_document = [{
            "Rules": [
                {
                    "ResourceType": "collection", 
                    "Resource": [f"collection/{collection_name}"], 
                    "Permission": [
                        "aoss:DescribeCollectionItems",
                        "aoss:CreateCollectionItems"
                    ]
                }, 
                {
                    "ResourceType": "index", 
                    "Resource": [f"index/{collection_name}/*"], 
                    "Permission": [
                        "aoss:ReadDocument",
                        "aoss:WriteDocument", 
                        "aoss:CreateIndex",
                        "aoss:DescribeIndex",
                        "aoss:UpdateIndex"
                    ]
                }
            ], 
            "Principal": [
                f"arn:aws:iam::{self.account}:root", 
                ingestion_lambda.role.role_arn,
                chatbot_lambda.role.role_arn,
                quiz_lambda.role.role_arn,
                progress_lambda.role.role_arn,
                recommendation_lambda.role.role_arn,
                f"arn:aws:iam::{self.account}:user/Admin1"
            ], 
            "Description": "Updated data access policy for ProCert OpenSearch - includes all Lambda functions that need access including quiz service"
        }]
        access_policy = opensearchserverless.CfnAccessPolicy(self, "ProcertAccessPolicy", name="procert-access-policy-v2", policy=json.dumps(access_policy_document), type="data")
        
        # Add vector collection dependencies
        self.vector_collection.add_dependency(access_policy)

        # 11. ENHANCED API GATEWAY WITH VALIDATION AND CORS
        api = apigateway.RestApi(self, "ProcertApi",
            rest_api_name="ProCert Learning Platform API",
            description="Enhanced API for ProCert Learning Platform with validation and comprehensive CORS support.",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "https://*.procert.app", "https://procert.app"],
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=[
                    "Content-Type", 
                    "X-Amz-Date", 
                    "Authorization", 
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                    "X-Requested-With",
                    "Accept",
                    "Origin",
                    "Referer"
                ],
                expose_headers=["X-Request-Id", "X-Rate-Limit-Remaining"],
                allow_credentials=True,
                max_age=Duration.hours(1)
            )
        )

        # Create request validators
        body_validator = api.add_request_validator("BodyValidator",
            validate_request_body=True,
            validate_request_parameters=False
        )
        
        params_validator = api.add_request_validator("ParamsValidator",
            validate_request_body=False,
            validate_request_parameters=True
        )
        
        full_validator = api.add_request_validator("FullValidator",
            validate_request_body=True,
            validate_request_parameters=True
        )

        # Essential JSON Schema models for validation
        # Quiz generation request model
        quiz_generate_model = api.add_model("QuizGenerateModel",
            content_type="application/json",
            model_name="QuizGenerateRequest",
            schema=apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                title="Quiz Generation Request",
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    "certification_type": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        enum=["general", "ccp", "aip", "saa", "dva", "soa", "mla", "dea", "dop", "sap", "mls", "scs", "ans"]
                    ),
                    "difficulty": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        enum=["beginner", "intermediate", "advanced"]
                    ),
                    "count": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.INTEGER,
                        minimum=5,
                        maximum=20
                    ),
                    "user_id": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        min_length=1,
                        max_length=128
                    )
                },
                required=["certification_type", "user_id"]
            )
        )

        # Quiz submission request model
        quiz_submit_model = api.add_model("QuizSubmitModel",
            content_type="application/json",
            model_name="QuizSubmitRequest",
            schema=apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                title="Quiz Submission Request",
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    "quiz_id": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        pattern="^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"
                    ),
                    "answers": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.ARRAY,
                        items=apigateway.JsonSchema(
                            type=apigateway.JsonSchemaType.OBJECT,
                            properties={
                                "question_id": apigateway.JsonSchema(
                                    type=apigateway.JsonSchemaType.STRING
                                ),
                                "selected_answer": apigateway.JsonSchema(
                                    type=apigateway.JsonSchemaType.STRING
                                )
                            },
                            required=["question_id", "selected_answer"]
                        ),
                        min_items=1,
                        max_items=20
                    ),
                    "user_id": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        min_length=1,
                        max_length=128
                    )
                },
                required=["quiz_id", "answers", "user_id"]
            )
        )

        # Create JWT authorizer
        jwt_authorizer = apigateway.TokenAuthorizer(self, "JWTAuthorizer",
            handler=jwt_authorizer_lambda,
            identity_source="method.request.header.Authorization",
            authorizer_name="ProcertJWTAuthorizer",
            results_cache_ttl=Duration.minutes(5)
        )

        # Chat endpoints (protected)
        chat_integration = apigateway.LambdaIntegration(chatbot_lambda)
        chat_resource = api.root.add_resource("chat")
        
        # POST /chat/message - Send message (protected)
        message_resource = chat_resource.add_resource("message")
        message_resource.add_method("POST", chat_integration, authorizer=jwt_authorizer)
        
        # GET /chat/conversation/{id} - Get conversation (protected)
        conversation_resource = chat_resource.add_resource("conversation")
        conversation_id_resource = conversation_resource.add_resource("{id}")
        conversation_id_resource.add_method("GET", chat_integration, authorizer=jwt_authorizer)
        
        # DELETE /chat/conversation/{id} - Delete conversation (protected)
        conversation_id_resource.add_method("DELETE", chat_integration, authorizer=jwt_authorizer)

        # User authentication and profile endpoints
        user_profile_integration = apigateway.LambdaIntegration(user_profile_lambda)
        
        # Authentication endpoints (public)
        auth_resource = api.root.add_resource("auth")
        auth_resource.add_resource("register").add_method("POST", user_profile_integration)
        auth_resource.add_resource("login").add_method("POST", user_profile_integration)
        auth_resource.add_resource("forgot-password").add_method("POST", user_profile_integration)
        auth_resource.add_resource("confirm-forgot-password").add_method("POST", user_profile_integration)
        
        # Profile management endpoints (protected)
        profile_resource = api.root.add_resource("profile")
        profile_user_resource = profile_resource.add_resource("{user_id}")
        profile_user_resource.add_method("GET", user_profile_integration, authorizer=jwt_authorizer)
        profile_user_resource.add_method("PUT", user_profile_integration, authorizer=jwt_authorizer)
        profile_user_resource.add_method("DELETE", user_profile_integration, authorizer=jwt_authorizer)

        # Quiz endpoints (protected) - simplified integration like profile endpoints
        quiz_integration = apigateway.LambdaIntegration(quiz_lambda)
        
        quiz_resource = api.root.add_resource("quiz")
        
        # POST /quiz/generate - Generate new quiz (protected)
        quiz_generate_resource = quiz_resource.add_resource("generate")
        quiz_generate_resource.add_method("POST", quiz_integration, authorizer=jwt_authorizer)
        
        # POST /quiz/submit - Submit quiz answers (protected)
        quiz_submit_resource = quiz_resource.add_resource("submit")
        quiz_submit_resource.add_method("POST", quiz_integration, authorizer=jwt_authorizer)
        
        # GET /quiz/history/{user_id} - Get quiz history (protected)
        quiz_history_resource = quiz_resource.add_resource("history")
        quiz_history_user_resource = quiz_history_resource.add_resource("{user_id}")
        quiz_history_user_resource.add_method("GET", quiz_integration, authorizer=jwt_authorizer)
        
        # GET /quiz/{quiz_id} - Get quiz details (protected)
        quiz_id_resource = quiz_resource.add_resource("{quiz_id}")
        quiz_id_resource.add_method("GET", quiz_integration, authorizer=jwt_authorizer)

        # Progress tracking endpoints (protected)
        progress_integration = apigateway.LambdaIntegration(progress_lambda)
        progress_resource = api.root.add_resource("progress")
        progress_user_resource = progress_resource.add_resource("{user_id}")

        # POST /progress/{user_id}/interaction - Record interaction (protected)
        interaction_resource = progress_user_resource.add_resource("interaction")
        interaction_resource.add_method("POST", progress_integration, authorizer=jwt_authorizer)

        # GET /progress/{user_id}/analytics - Get performance analytics (protected)
        analytics_resource = progress_user_resource.add_resource("analytics")
        analytics_resource.add_method("GET", progress_integration, authorizer=jwt_authorizer)

        # GET /progress/{user_id}/trends - Get performance trends (protected)
        trends_resource = progress_user_resource.add_resource("trends")
        trends_resource.add_method("GET", progress_integration, authorizer=jwt_authorizer)

        # GET /progress/{user_id}/readiness - Get certification readiness (protected)
        readiness_resource = progress_user_resource.add_resource("readiness")
        readiness_resource.add_method("GET", progress_integration, authorizer=jwt_authorizer)

        # GET /progress/{user_id}/achievements - Get user achievements (protected)
        achievements_resource = progress_user_resource.add_resource("achievements")
        achievements_resource.add_method("GET", progress_integration, authorizer=jwt_authorizer)

        # GET /progress/{user_id}/dashboard - Get comprehensive dashboard data (protected)
        dashboard_resource = progress_user_resource.add_resource("dashboard")
        dashboard_resource.add_method("GET", progress_integration, authorizer=jwt_authorizer)

        # Recommendation endpoints (protected)
        recommendation_integration = apigateway.LambdaIntegration(recommendation_lambda)
        recommendations_resource = api.root.add_resource("recommendations")
        recommendations_user_resource = recommendations_resource.add_resource("{user_id}")

        # GET /recommendations/{user_id} - Get personalized recommendations (protected)
        recommendations_user_resource.add_method("GET", recommendation_integration, authorizer=jwt_authorizer)

        # GET /recommendations/{user_id}/study-path - Get personalized study path (protected)
        study_path_resource = recommendations_user_resource.add_resource("study-path")
        study_path_resource.add_method("GET", recommendation_integration, authorizer=jwt_authorizer)

        # POST /recommendations/{user_id}/feedback - Record recommendation feedback (protected)
        feedback_resource = recommendations_user_resource.add_resource("feedback")
        feedback_resource.add_method("POST", recommendation_integration, authorizer=jwt_authorizer)

        # GET /recommendations/{user_id}/weak-areas - Get weak areas analysis (protected)
        weak_areas_resource = recommendations_user_resource.add_resource("weak-areas")
        weak_areas_resource.add_method("GET", recommendation_integration, authorizer=jwt_authorizer)

        # GET /recommendations/{user_id}/content-progression - Get content difficulty progression (protected)
        content_progression_resource = recommendations_user_resource.add_resource("content-progression")
        content_progression_resource.add_method("GET", recommendation_integration, authorizer=jwt_authorizer)

        # Maintain backward compatibility
        query_resource = api.root.add_resource("query")
        query_resource.add_method("POST", chat_integration)

        # CREATE OPENSEARCH SERVERLESS ACCESS POLICY
        # This grants the Lambda functions access to the OpenSearch collection
        collection_name = "procert-vector-collection"
        lambda_roles = [
            ingestion_lambda.role.role_arn,
            chatbot_lambda.role.role_arn,
            quiz_lambda.role.role_arn,
            progress_lambda.role.role_arn,
            recommendation_lambda.role.role_arn,
            index_setup_lambda.role.role_arn
        ]
        
        access_policy = opensearchserverless.CfnAccessPolicy(self, "ProcertDataAccessPolicy",
            name="procert-data-access-policy",
            type="data",
            policy=json.dumps([{
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems", 
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems"
                        ]
                    },
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{collection_name}/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument"
                        ]
                    }
                ],
                "Principal": lambda_roles
            }])
        )
        
        # Add dependency so access policy is created before collection
        self.vector_collection.add_dependency(access_policy)

        CfnOutput(self, "ApiEndpoint", value=api.url)
        CfnOutput(self, "ProgressLambdaArn", value=progress_lambda.function_arn)
        CfnOutput(self, "RecommendationLambdaArn", value=recommendation_lambda.function_arn)