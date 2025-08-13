# CDK Integration Code for Enhanced Progress Tracking Lambda
# Add this code to procert_infrastructure_stack.py

# Add after the quiz lambda section (around line 650)

# 10.7. ENHANCED PROGRESS TRACKING LAMBDA
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
        "CONTENT_METADATA_TABLE_NAME": self.content_metadata_table.table_name,
        "AWS_REGION": self.region
    }
)

# Grant DynamoDB permissions to progress lambda
self.user_progress_table.grant_read_write_data(progress_lambda)
self.content_metadata_table.grant_read_data(progress_lambda)

# Add after the existing API Gateway endpoints (around line 750)

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

# Add output for the progress lambda
CfnOutput(self, "ProgressLambdaArn", value=progress_lambda.function_arn)