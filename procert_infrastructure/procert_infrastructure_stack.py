# procert_infrastructure/procert_infrastructure_stack.py

from aws_cdk import (
    Stack, RemovalPolicy, CfnOutput, Duration, BundlingOptions, CustomResource,
    aws_s3 as s3, aws_s3_notifications as s3_notifications,
    aws_opensearchserverless as opensearchserverless,
    aws_lambda as lambda_, aws_iam as iam,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
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
            table_name=f"procert-content-metadata-v2-{self.account}",
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

        # User profiles table
        self.user_profiles_table = dynamodb.Table(self, "UserProfilesTable",
            table_name=f"procert-user-profiles-{self.account}",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED
        )

        # Add GSI for querying by email (for login)
        self.user_profiles_table.add_global_secondary_index(
            index_name="EmailIndex",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Add GSI for querying by subscription tier
        self.user_profiles_table.add_global_secondary_index(
            index_name="SubscriptionTierIndex",
            partition_key=dynamodb.Attribute(
                name="subscription_tier",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
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
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl"  # Enable TTL for automatic cleanup
        )

        # Add GSI for querying user's quiz sessions
        self.quiz_sessions_table.add_global_secondary_index(
            index_name="UserQuizIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Output table names
        CfnOutput(self, "ContentMetadataTableName", value=self.content_metadata_table.table_name)
        CfnOutput(self, "UserProgressTableName", value=self.user_progress_table.table_name)
        CfnOutput(self, "ConversationTableName", value=self.conversation_table.table_name)
        CfnOutput(self, "UserProfilesTableName", value=self.user_profiles_table.table_name)
        CfnOutput(self, "QuizSessionsTableName", value=self.quiz_sessions_table.table_name)

        # 4. AWS COGNITO USER AUTHENTICATION
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
            # Standard attributes
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=True, mutable=True),
                family_name=cognito.StandardAttribute(required=True, mutable=True)
            ),
            # Custom attributes for certification preferences
            custom_attributes={
                "target_certs": cognito.StringAttribute(mutable=True)  # Shortened to fit 20-char limit
            }
        )

        # User Pool Client for web application
        self.user_pool_client = cognito.UserPoolClient(self, "ProcertUserPoolClient",
            user_pool=self.user_pool,
            user_pool_client_name=f"procert-web-client-{self.account}",
            generate_secret=False,  # For web applications
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=["http://localhost:3000/auth/callback", "https://procert.example.com/auth/callback"]
            ),
            refresh_token_validity=Duration.days(30),
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1)
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
            )
        )

        # Attach policy to authenticated role for API Gateway access
        authenticated_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["execute-api:Invoke"],
            resources=[f"arn:aws:execute-api:{self.region}:{self.account}:*"]
        ))

        # Role attachment for Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(self, "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={
                "authenticated": authenticated_role.role_arn
            }
        )

        # SAML Identity Provider for Midway integration (optional)
        # Uncomment and configure when Midway SAML metadata is available
        # midway_saml_provider = cognito.CfnUserPoolIdentityProvider(self, "MidwaySAMLProvider",
        #     user_pool_id=self.user_pool.user_pool_id,
        #     provider_name="Midway",
        #     provider_type="SAML",
        #     attribute_mapping={
        #         "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        #         "given_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
        #         "family_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
        #     },
        #     provider_details={
        #         "MetadataURL": "https://midway.amazon.com/saml/metadata",  # Replace with actual Midway metadata URL
        #         "SSORedirectBindingURI": "https://midway.amazon.com/saml/sso",  # Replace with actual SSO URL
        #         "SLORedirectBindingURI": "https://midway.amazon.com/saml/slo"   # Replace with actual SLO URL
        #     }
        # )

        # Update User Pool Client to support federated sign-in
        # When Midway is configured, update the client:
        # self.user_pool_client.add_property_override("SupportedIdentityProviders", ["COGNITO", "Midway"])

        # Output Cognito details
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
        CfnOutput(self, "IdentityPoolId", value=self.identity_pool.ref)
        
        # 5. OPENSEARCH SERVERLESS SETUP
        collection_name = "procert-vector-collection"
        access_policy_document = [{"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"], "Permission": ["aoss:*"]}, {"ResourceType": "index", "Resource": [f"index/{collection_name}/*"], "Permission": ["aoss:*"]}], "Principal": [f"arn:aws:iam::{self.account}:root", ingestion_lambda.role.role_arn, f"arn:aws:iam::{self.account}:user/Admin1"], "Description": "Data access policy for ProCert"}]
        # Use simple unique names (max 32 chars, pattern: ^[a-z][a-z0-9-]{2,31}$)
        import time
        suffix = str(int(time.time()))[-6:]  # Use timestamp suffix for uniqueness
        access_policy = opensearchserverless.CfnAccessPolicy(self, "ProcertAccessPolicy", name=f"procert-access-{suffix}", policy=json.dumps(access_policy_document), type="data")
        
        encryption_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertEncryptionPolicy", name=f"procert-encrypt-{suffix}", type="encryption", policy=json.dumps({"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}], "AWSOwnedKey": True}))
        
        network_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertNetworkPolicy", name=f"procert-network-{suffix}", type="network", policy=json.dumps([{"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}, {"ResourceType": "dashboard", "Resource": [f"collection/{collection_name}"]}], "AllowFromPublic": True}]))
        
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
            # In CI, use simple asset bundling but ensure dependencies are available
            index_lambda_code = lambda_.Code.from_asset("index_setup_lambda_src")
        else:
            index_lambda_code = lambda_.Code.from_asset("index_setup_lambda_src",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    entrypoint=["/bin/bash", "-c"],
                    command=["pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements.txt -t /asset-output && cp -au . /asset-output"]
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
            description="Handles user profile management and authentication for the ProCert Learning Platform.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.lambda_handler",
            code=user_profile_lambda_code,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "USER_PROFILES_TABLE": self.user_profiles_table.table_name,
                "QUIZ_SESSIONS_TABLE": self.quiz_sessions_table.table_name,
                "USER_POOL_ID": self.user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": self.user_pool_client.user_pool_client_id
            }
        )

        # Grant DynamoDB permissions to user profile lambda
        self.user_profiles_table.grant_read_write_data(user_profile_lambda)
        self.quiz_sessions_table.grant_read_write_data(user_profile_lambda)
        
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

        # 10.6. JWT AUTHORIZER LAMBDA
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
            description="JWT token authorizer for API Gateway authentication.",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.handler",
            code=jwt_authorizer_lambda_code,
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={
                "USER_POOL_ID": self.user_pool.user_pool_id
            }
        )

        # Grant Cognito permissions to JWT authorizer lambda
        jwt_authorizer_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["cognito-idp:GetUser"],
            resources=[self.user_pool.user_pool_arn]
        ))

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

        # JWT Authorizer for protected endpoints
        jwt_authorizer = apigateway.TokenAuthorizer(self, "JWTAuthorizer",
            handler=jwt_authorizer_lambda,
            identity_source="method.request.header.Authorization",
            authorizer_name="ProcertJWTAuthorizer",
            results_cache_ttl=Duration.minutes(5)
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

        # User profile and authentication endpoints
        user_profile_integration = apigateway.LambdaIntegration(user_profile_lambda)
        
        # Authentication endpoints
        auth_resource = api.root.add_resource("auth")
        
        # POST /auth/register - User registration
        register_resource = auth_resource.add_resource("register")
        register_resource.add_method("POST", user_profile_integration)
        
        # POST /auth/login - User login
        login_resource = auth_resource.add_resource("login")
        login_resource.add_method("POST", user_profile_integration)
        
        # POST /auth/forgot-password - Forgot password
        forgot_password_resource = auth_resource.add_resource("forgot-password")
        forgot_password_resource.add_method("POST", user_profile_integration)
        
        # POST /auth/confirm-forgot-password - Confirm forgot password
        confirm_forgot_password_resource = auth_resource.add_resource("confirm-forgot-password")
        confirm_forgot_password_resource.add_method("POST", user_profile_integration)
        
        # Profile management endpoints (protected with JWT authorizer)
        profile_resource = api.root.add_resource("profile")
        profile_user_resource = profile_resource.add_resource("{user_id}")
        
        # GET /profile/{user_id} - Get user profile
        profile_user_resource.add_method("GET", user_profile_integration,
            authorizer=jwt_authorizer
        )
        
        # PUT /profile/{user_id} - Update user profile
        profile_user_resource.add_method("PUT", user_profile_integration,
            authorizer=jwt_authorizer
        )
        
        # DELETE /profile/{user_id} - Delete user profile
        profile_user_resource.add_method("DELETE", user_profile_integration,
            authorizer=jwt_authorizer
        )

        CfnOutput(self, "ApiEndpoint", value=api.url)