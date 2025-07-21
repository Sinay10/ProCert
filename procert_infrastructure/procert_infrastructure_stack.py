# procert_infrastructure/procert_infrastructure_stack.py

from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Duration,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_opensearchserverless as opensearchserverless,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct
import json

class ProcertInfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. LAMBDA FOR DATA INGESTION
        # Defined first so its role can be referenced in other policies.
        ingestion_lambda = lambda_.Function(self, "ProcertIngestionLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="main.handler",
            code=lambda_.Code.from_asset("lambda_src"),
            timeout=Duration.seconds(300),
            memory_size=512,
            environment={
                # We will add the endpoint after the collection is defined
            }
        )

        # 2. S3 BUCKET
        self.materials_bucket = s3.Bucket(self, "CertificationMaterialsBucket",
            bucket_name=f"procert-materials-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )
        CfnOutput(self, "MaterialsBucketName", value=self.materials_bucket.bucket_name,
            description="The name of the S3 bucket for storing certification materials.")
        
        # ADDED: S3 bucket policy to enforce secure transport
        self.materials_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[self.materials_bucket.arn_for_objects("*")],
                conditions={
                    "Bool": {"aws:SecureTransport": "false"}
                }
            )
        )
        self.materials_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[self.materials_bucket.arn_for_objects("*")],
                conditions={
                     "NumericLessThan": {"s3:TlsVersion": "1.2"}
                }
            )
        )
        
        # 3. OPENSEARCH SERVERLESS SETUP
        collection_name = "procert-vector-collection"

        # UPDATED: Data access policy now includes the Lambda's specific role
        access_policy_document = [
            {
                "Rules": [
                    {"ResourceType": "collection", "Resource": [f"collection/{collection_name}"], "Permission": ["aoss:*"]},
                    {"ResourceType": "index", "Resource": [f"index/{collection_name}/*"], "Permission": ["aoss:*"]}
                ],
                "Principal": [
                    f"arn:aws:iam::{self.account}:root",
                    ingestion_lambda.role.role_arn
                ],
                "Description": "Data access policy for ProCert"
            }
        ]
        access_policy = opensearchserverless.CfnAccessPolicy(self, "ProcertAccessPolicy", name="procert-access-policy", policy=json.dumps(access_policy_document), type="data")
        
        encryption_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertEncryptionPolicy", name="procert-encryption-policy", type="encryption", policy=json.dumps({"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}], "AWSOwnedKey": True}))
        network_policy = opensearchserverless.CfnSecurityPolicy(self, "ProcertNetworkPolicy", name="procert-network-policy", type="network", policy=json.dumps([{"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]},], "AllowFromPublic": True}]))
        
        self.vector_collection = opensearchserverless.CfnCollection(self, "VectorCollection", name=collection_name, type="VECTORSEARCH", description="Stores vector embeddings for ProCert documents.")
        self.vector_collection.add_dependency(access_policy)
        self.vector_collection.add_dependency(encryption_policy)
        self.vector_collection.add_dependency(network_policy)
        CfnOutput(self, "OpenSearchCollectionEndpoint", value=self.vector_collection.attr_collection_endpoint,
            description="The endpoint for the OpenSearch Serverless collection.")

        # ADDED: Pass the collection endpoint to the Lambda function's environment
        ingestion_lambda.add_environment("OPENSEARCH_ENDPOINT", self.vector_collection.attr_collection_endpoint)
        ingestion_lambda.add_environment("OPENSEARCH_INDEX", collection_name)
        
        # 4. S3 TRIGGER FOR THE LAMBDA
        self.materials_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(ingestion_lambda),
            s3.NotificationKeyFilter(suffix=".pdf")
        )
        self.materials_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(ingestion_lambda),
            s3.NotificationKeyFilter(suffix=".docx")
        )

        # 5. GRANT PERMISSIONS TO THE LAMBDA
        self.materials_bucket.grant_read(ingestion_lambda)
        ingestion_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1"]
        ))
        ingestion_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["aoss:APIAccessAll"],
            resources=[self.vector_collection.attr_arn]
        ))