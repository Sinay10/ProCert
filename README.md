
# ProCert - AWS Certification Study Platform

<div align="center">

*An intelligent AWS certification study platform powered by RAG technology*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![AWS CDK](https://img.shields.io/badge/AWS%20CDK-2.210.0+-orange.svg)](https://aws.amazon.com/cdk/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-Educational-green.svg)](#license)

</div>

## 🎯 Overview

ProCert is an intelligent AWS certification study platform that leverages **RAG (Retrieval-Augmented Generation)** technology to provide personalized learning experiences for AWS certification candidates. Built with modern serverless architecture, it offers adaptive learning paths, intelligent content processing, and comprehensive progress tracking.

### Key Features

- **AI-Powered Chatbot** - Context-aware responses using Amazon Bedrock
- **Multi-Certification Support** - SAA, DVA, SOA, and more AWS certifications  
- **Intelligent Content Processing** - Automatic PDF extraction and categorization
- **Progress Tracking** - Comprehensive analytics and performance insights
- **Adaptive Quizzes** - Personalized question selection based on weak areas
- **Semantic Search** - Vector-based content retrieval with OpenSearch

## Quick Start

### 1.1. Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate permissions
- AWS CDK 2.210.0+
- Node.js 18+ (for CDK)
- Git access to the repository

### 1.2. One-Time Setup (Required)

1. **Clone the repository**:
   ```bash
   git clone ssh://ssh.gitlab.aws.dev/ymarouaz/ProCert.git
   cd ProCert
   ```

2. **Set up Python environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install CDK dependencies**:
   ```bash
   npm install -g aws-cdk@2.210.0
   ```

4. **Bootstrap CDK** (first time only):
   ```bash
   cdk bootstrap
   ```

### 1.3. Deploy Application

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy to AWS
cdk deploy --all

# View deployment differences
cdk diff
```

### 1.4. Access Your Application

After deployment, the application will be available through:
- **API Gateway Endpoint**: Available in CDK outputs
- **Frontend URL**: Available in CDK outputs
- **Health Check**: `GET /health` endpoint

## Detailed Setup Guide

### Prerequisites

#### AWS CLI Requirements

ProCert uses OpenSearch Serverless for cost-effective vector storage, which requires a recent AWS CLI version.

**Minimum Requirements:**
- AWS CLI Version: 2.27.57 or later
- Python: 3.11+ (for CDK and deployment scripts)
- Node.js: 18+ (for frontend development)

**Quick Check:**
```bash
# Check your current AWS CLI version
aws --version
# Should show: aws-cli/2.27.57 or higher
```

#### Installation/Update Instructions

**macOS (Homebrew):**
```bash
brew install awscli && brew upgrade awscli
aws --version
```

**Linux/macOS (pip):**
```bash
pip install --upgrade awscli
aws --version
```

**Official Installer:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install --update
aws --version
```

#### AWS Configuration

**Configure AWS Credentials:**
```bash
aws configure
```
Enter:
- AWS Access Key ID
- Secret Access Key
- Default region (e.g., us-east-1)
- Output format (json)

**Verify Configuration:**
```bash
aws sts get-caller-identity  # Test credentials
aws opensearch help          # Test OpenSearch support
```

#### CDK Configuration (Optional)

CDK automatically uses your AWS CLI configured account and region. If you encounter deployment issues, you can explicitly set them in `cdk.json`:

```json
{
  "context": {
    "account": "123456789012",  // Replace with your AWS account ID
    "region": "us-east-1"       // Replace with your preferred region
  }
}
```

**Get your account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

#### Automated Prerequisites Check

```bash
# Run full environment check
python3 scripts/check_prerequisites.py

# Quick version check only
python3 scripts/check_prerequisites.py --version-only
```

#### Common Issues & Solutions

| Issue | Problem | Solution |
|-------|---------|----------|
| "OpenSearch command not found" | AWS CLI version too old | Update AWS CLI to 2.27.57+ |
| "No credentials found" | AWS credentials not configured | Run `aws configure` |
| "Region not specified" | No default region set | `aws configure set region us-east-1` |
| "CDK bootstrap failed" | Account/region mismatch | Verify account ID and region |
| "Permission denied" | Insufficient AWS permissions | Check IAM permissions for deployment |

## Content Upload (Required for Full Functionality)

### 2.1. Exam Path Documents

Upload your source certification documents to the S3 bucket created during deployment. Supported formats:
- PDF files containing exam guides
- Study materials in PDF format
- Practice questions and answers

### 2.2. Exam Guides

The system automatically processes and categorizes exam guides based on:
- AWS certification type detection
- Content structure analysis
- Metadata extraction

### 2.3. Practice Questions

Upload practice questions in supported formats. The system will:
- Extract questions and answers
- Categorize by certification type
- Index for semantic search

### 2.4. Study Materials

Additional study materials can be uploaded including:
- Whitepapers
- Documentation excerpts
- Custom study notes

### 2.5. Verify Content Upload

Monitor content processing through:
```bash
# Check processing status
python scripts/verify_content_upload.py

# View indexed content
python scripts/list_indexed_content.py
```

## Development Mode (Optional)

For local development and testing:

```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ -v --cov=shared --cov-report=html

# Run integration tests
python test_lambda_integration.py
python test_certification_extraction.py

# Test Docker bundling for Lambda functions
python scripts/test_docker_bundling.py

# Run comprehensive pre-deployment tests
python scripts/test_deployment.py
```

## Cleanup

To remove all AWS resources:

```bash
# Destroy all stacks
cdk destroy --all

# Clean up local environment
deactivate
rm -rf .venv
```

## Overview

### 5.1. Architecture Flow

<div align="center">

![Architecture Flow](assets/screenshots/architecture-diagram.png)

</div>

The ProCert platform follows a serverless architecture pattern:

1. **Content Ingestion**: Documents uploaded to S3 trigger Lambda processing
2. **Vector Processing**: Content is embedded using Amazon Bedrock Titan
3. **Storage**: Metadata stored in DynamoDB, vectors in OpenSearch Serverless
4. **Query Processing**: User queries processed through RAG pipeline
5. **Response Generation**: Claude 3.5 Sonnet generates contextual responses

### 5.2. Key Features

- **Multi-Certification Support**: SAA, DVA, SOA, and more AWS certifications
- **Intelligent Content Processing**: Automatic extraction and categorization of study materials
- **RAG-Powered Chatbot**: AI-powered assistant for answering certification questions
- **Progress Tracking**: Comprehensive user progress and performance analytics
- **Content Management**: Structured storage and retrieval of questions, study guides, and practice exams
- **Certification-Aware Architecture**: Content filtering and recommendations based on certification type

#### Study Path Management

![Study Path](assets/screenshots/study-path.png)

The study path feature allows users to follow structured learning paths tailored to specific AWS certifications.

#### Progress Tracking

![Progress Screen](assets/screenshots/progress-tracking.png)

Comprehensive progress tracking shows user performance across different topics and certification areas.

## Architecture

### 6.1. Features

#### Chat Interface

![Chatbot Interface](assets/screenshots/chatbot-interface.png)

The chat interface provides:
- Natural language query processing
- Context-aware responses based on uploaded content
- Certification-specific filtering
- Conversation history and context retention

#### Quiz System

![Quiz Interface](assets/screenshots/quiz-system.png)

Interactive quiz functionality includes:
- Adaptive question selection
- Real-time feedback and explanations
- Progress tracking and analytics
- Performance-based recommendations

#### Dashboard Overview

![Dashboard](assets/screenshots/dashboard.png)

The main dashboard provides:
- Overview of study progress across certifications
- Quick access to key features and resources
- Performance metrics and recommendations
- Recent activity and achievements

#### Content Management

![Resources Management](assets/screenshots/resources-management.png)

Comprehensive content management system:
- Automated document processing
- Metadata extraction and categorization
- Content versioning and updates
- Search and filtering capabilities

#### Technical Features

- **Vector Search**: OpenSearch Serverless for semantic content retrieval
- **AI Integration**: Amazon Bedrock for embeddings and chat responses
- **Scalable Storage**: DynamoDB for metadata and user progress tracking
- **Serverless Compute**: AWS Lambda for all processing functions
- **API Layer**: API Gateway with comprehensive endpoint management

## Development

### 7.1. Frontend Development

The frontend is built with modern web technologies:

```bash
cd frontend
npm install
npm run dev
```

Key frontend components:
- React-based user interface
- TypeScript for type safety
- Responsive design for mobile and desktop
- Real-time chat interface

### 7.2. Backend Development

Backend services are implemented as AWS Lambda functions:

```
lambda_src/                     # Content ingestion Lambda
chatbot_lambda_src/             # Chatbot Lambda function
quiz_lambda_src/                # Quiz system Lambda
user_profile_lambda_src/        # User management Lambda
progress_lambda_src/            # Progress tracking Lambda
recommendation_lambda_src/      # Recommendation engine Lambda
```

### 7.3. Infrastructure Development

Infrastructure is managed through AWS CDK:

```bash
# View current infrastructure
cdk ls

# Deploy specific stack
cdk deploy ProCertStack

# View infrastructure differences
cdk diff
```

## Configuration

### 8.1. Environment Variables

The application uses the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENSEARCH_ENDPOINT` | OpenSearch cluster endpoint | Yes |
| `OPENSEARCH_INDEX` | Index name for vector storage | Yes |
| `CONTENT_METADATA_TABLE` | DynamoDB table for content metadata | Yes |
| `USER_PROGRESS_TABLE` | DynamoDB table for user progress | Yes |
| `BEDROCK_REGION` | AWS region for Bedrock services | Yes |
| `S3_BUCKET_NAME` | S3 bucket for content storage | Yes |

### 8.2. Infrastructure Settings

Key infrastructure configurations:

- **OpenSearch Serverless**: Configured for vector search with appropriate capacity
- **DynamoDB**: On-demand billing with global secondary indexes
- **Lambda**: Python 3.11 runtime with appropriate memory and timeout settings
- **API Gateway**: REST API with CORS enabled and rate limiting
- **VPC**: Secure networking configuration for Lambda functions

## Monitoring

### 9.1. Health Monitoring

Monitor application health through:

```bash
# Check application health
curl https://your-api-gateway-url/health

# Monitor AWS costs
python scripts/cost_monitor.py

# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ProCert"
```

### 9.2. Key Metrics

Important metrics to monitor:

- **Lambda Function Duration**: Processing time for each function
- **API Gateway Latency**: Response times for API calls
- **OpenSearch Query Performance**: Search query execution times
- **DynamoDB Throttling**: Read/write capacity utilization
- **Error Rates**: Function error rates and types

**Current Architecture Costs**:
- OpenSearch Serverless: ~$42/month (primary cost)
- VPC & Networking: ~$7/month
- Lambda & API Gateway: Minimal (within free tier)
- DynamoDB: Minimal (within free tier)
- S3: Minimal (within free tier)

## Project Structure

```
procert-infrastructure/
├── shared/                          # Shared models and interfaces
│   ├── models.py                   # Data models (ContentMetadata, UserProgress, etc.)
│   ├── interfaces.py               # Service interfaces
│   ├── storage_manager.py          # DynamoDB storage implementation
│   └── README.md                   # Shared module documentation
├── lambda_src/                     # Content ingestion Lambda
├── chatbot_lambda_src/             # Chatbot Lambda function
├── quiz_lambda_src/                # Quiz system Lambda
├── user_profile_lambda_src/        # User management Lambda
├── progress_lambda_src/            # Progress tracking Lambda
├── recommendation_lambda_src/      # Recommendation engine Lambda
├── index_setup_lambda_src/         # OpenSearch index setup
├── procert_infrastructure/         # CDK infrastructure code
├── frontend/                       # React frontend application
├── tests/                          # Unit and integration tests
├── scripts/                        # Utility scripts
│   ├── cost_monitor.py            # AWS cost monitoring
│   └── setup_aws_gitlab_ssh.sh    # GitLab SSH setup
└── docs/                          # Documentation
```

##
 Certification Types Supported

The platform supports multiple AWS certification paths:

- **CCP**: AWS Certified Cloud Practitioner
- **SAA**: AWS Certified Solutions Architect - Associate
- **DVA**: AWS Certified Developer - Associate
- **SOA**: AWS Certified SysOps Administrator - Associate
- **DOP**: AWS Certified DevOps Engineer - Professional
- **SAP**: AWS Certified Solutions Architect - Professional
- **ANS**: AWS Certified Advanced Networking - Specialty
- **SCS**: AWS Certified Security - Specialty
- **DAS**: AWS Certified Data Analytics - Specialty
- **MLS**: AWS Certified Machine Learning - Specialty

## Testing

The project includes comprehensive testing coverage:

- **Unit Tests**: 23+ tests covering core functionality
- **Integration Tests**: End-to-end testing with LocalStack
- **Security Tests**: Automated security scanning with Bandit
- **Coverage**: >80% code coverage target

### Test Categories

- **Lambda Function Tests**: Individual function testing
- **Storage Layer Tests**: DynamoDB and OpenSearch integration
- **API Tests**: End-to-end API functionality
- **Security Tests**: Vulnerability scanning and compliance

## Security

Security is implemented at multiple layers:

- **IAM Roles**: Least privilege access for all components
- **VPC**: Secure networking with private subnets
- **Encryption**: Data encrypted at rest and in transit
- **Security Scanning**: Automated vulnerability detection with GitLab CI
- **Secret Management**: No hardcoded credentials, AWS Secrets Manager integration
- **API Security**: Rate limiting, input validation, and authentication

## Documentation

Comprehensive documentation is available:

- [Storage Manager Documentation](shared/storage_manager_README.md)
- [GitLab Setup Guide](docs/GITLAB_INTERN_SETUP.md)

- [Certification Detection Guide](CERTIFICATION_DETECTION.md)
- [Authentication Troubleshooting](docs/AUTHENTICATION_TROUBLESHOOTING_GUIDE.md)
- [Security Pipeline Integration](docs/SECURITY_PIPELINE_INTEGRATION.md)

## Contributing

1. Create a feature branch: `git checkout -b feature/new-feature`
2. Make your changes and add tests
3. Ensure all tests pass: `python -m pytest`
4. Run security scans: `python security_analysis_ci.py`
5. Create a merge request in GitLab

## Troubleshooting

Common issues and solutions:

### Deployment Issues
- Ensure AWS credentials are properly configured
- Verify CDK bootstrap has been completed
- Check CloudFormation stack events for detailed error messages

### Content Processing Issues
- Verify S3 bucket permissions
- Check Lambda function logs in CloudWatch
- Ensure content is in supported PDF format

### API Issues
- Check API Gateway logs
- Verify Lambda function permissions
- Test endpoints individually

## Support

For questions or issues:
- Create an issue in GitLab
- Check the documentation in the `docs/` directory
- Consult troubleshooting guides for common issues

## License

This project is for educational and personal use.

---

Built using AWS CDK, Python, and modern serverless architecture patterns.
