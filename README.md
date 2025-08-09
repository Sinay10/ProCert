
# ProCert - AWS Certification Study Platform

[![pipeline status](https://gitlab.aws.dev/ymarouaz/ProCert/badges/main/pipeline.svg)](https://gitlab.aws.dev/ymarouaz/ProCert/-/commits/main)
[![coverage report](https://gitlab.aws.dev/ymarouaz/ProCert/badges/main/coverage.svg)](https://gitlab.aws.dev/ymarouaz/ProCert/-/commits/main)

ProCert is an intelligent AWS certification study platform that leverages RAG (Retrieval-Augmented Generation) technology to provide personalized learning experiences for AWS certification candidates.

## 🚀 Features

- **Multi-Certification Support**: SAA, DVA, SOA, and more AWS certifications
- **Intelligent Content Processing**: Automatic extraction and categorization of study materials
- **RAG-Powered Chatbot**: AI-powered assistant for answering certification questions
- **Progress Tracking**: Comprehensive user progress and performance analytics
- **Content Management**: Structured storage and retrieval of questions, study guides, and practice exams
- **Certification-Aware Architecture**: Content filtering and recommendations based on certification type

## 🏗️ Architecture

### Core Components

- **Content Ingestion**: Lambda-based PDF processing and metadata extraction
- **Vector Search**: OpenSearch Serverless for semantic content retrieval
- **Storage Layer**: DynamoDB for metadata and user progress tracking
- **AI Integration**: Amazon Bedrock for embeddings and chat responses
- **API Layer**: API Gateway with Lambda functions for user interactions

### AWS Services Used

- **Compute**: AWS Lambda, API Gateway
- **Storage**: Amazon S3, DynamoDB, OpenSearch Serverless
- **AI/ML**: Amazon Bedrock (Titan Embeddings, Claude 3.5 Sonnet)
- **Infrastructure**: AWS CDK, CloudFormation
- **Security**: IAM, VPC, AWS WAF

## 📁 Project Structure

```
procert-infrastructure/
├── shared/                          # Shared models and interfaces
│   ├── models.py                   # Data models (ContentMetadata, UserProgress, etc.)
│   ├── interfaces.py               # Service interfaces
│   ├── storage_manager.py          # DynamoDB storage implementation
│   └── README.md                   # Shared module documentation
├── lambda_src/                     # Content ingestion Lambda
├── chatbot_lambda_src/             # Chatbot Lambda function
├── index_setup_lambda_src/         # OpenSearch index setup
├── procert_infrastructure/         # CDK infrastructure code
├── tests/                          # Unit and integration tests
├── scripts/                        # Utility scripts
│   ├── cost_monitor.py            # AWS cost monitoring
│   └── setup_aws_gitlab_ssh.sh    # GitLab SSH setup
├── docs/                          # Documentation
└── .kiro/specs/                   # Feature specifications
```

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- AWS CLI configured
- AWS CDK 2.210.0+
- Node.js 18+ (for CDK)

### Local Development

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

### Running Tests

```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ -v --cov=shared --cov-report=html

# Run integration tests
python test_lambda_integration.py
python test_certification_extraction.py
```

## 🚀 Deployment

### Using CDK

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy to AWS
cdk deploy --all

# View differences
cdk diff
```

### Using GitLab CI/CD

The project includes automated CI/CD pipeline that:
- Validates code quality (linting, formatting)
- Runs comprehensive test suite
- Performs security scanning
- Deploys to AWS (manual trigger)

## 📊 Monitoring & Cost Management

### Cost Monitoring

Monitor AWS costs with the built-in cost monitor:

```bash
python scripts/cost_monitor.py
```

### Current Architecture Costs

- **OpenSearch Serverless**: ~$42/month (primary cost)
- **VPC & Networking**: ~$7/month
- **Lambda & API Gateway**: Minimal (within free tier)
- **DynamoDB**: Minimal (within free tier)
- **S3**: Minimal (within free tier)

## 🔧 Configuration

### Environment Variables

The application uses the following environment variables:

- `OPENSEARCH_ENDPOINT`: OpenSearch cluster endpoint
- `OPENSEARCH_INDEX`: Index name for vector storage
- `CONTENT_METADATA_TABLE`: DynamoDB table for content metadata
- `USER_PROGRESS_TABLE`: DynamoDB table for user progress

### Certification Types Supported

- **CCP**: AWS Certified Cloud Practitioner
- **SAA**: AWS Certified Solutions Architect - Associate
- **DVA**: AWS Certified Developer - Associate
- **SOA**: AWS Certified SysOps Administrator - Associate
- **DOP**: AWS Certified DevOps Engineer - Professional
- **SAP**: AWS Certified Solutions Architect - Professional
- And more...

## 📚 Documentation

- [Storage Manager Documentation](shared/storage_manager_README.md)
- [GitLab Setup Guide](docs/GITLAB_INTERN_SETUP.md)
- [Content Management Specification](.kiro/specs/content-management/)
- [Certification Detection Guide](CERTIFICATION_DETECTION.md)

## 🧪 Testing

The project includes comprehensive testing:

- **Unit Tests**: 23+ tests covering core functionality
- **Integration Tests**: End-to-end testing with LocalStack
- **Security Tests**: Automated security scanning with Bandit
- **Coverage**: >80% code coverage target

## 🔒 Security

- **IAM Roles**: Least privilege access for all components
- **VPC**: Secure networking with private subnets
- **Encryption**: Data encrypted at rest and in transit
- **Security Scanning**: Automated vulnerability detection
- **Secret Management**: No hardcoded credentials

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/new-feature`
2. Make your changes and add tests
3. Ensure all tests pass: `python -m pytest`
4. Create a merge request in GitLab

## 📈 Roadmap

- [ ] Advanced analytics dashboard
- [ ] Mobile application support
- [ ] Multi-language content support
- [ ] Advanced recommendation engine
- [ ] Integration with AWS Training and Certification

## 📄 License

This project is for educational and personal use.

## 🆘 Support

For questions or issues:
- Create an issue in GitLab
- Check the documentation in the `docs/` directory
- Review the specifications in `.kiro/specs/`

---

**Built with ❤️ using AWS CDK, Python, and modern DevOps practices**
