# CDK Nag Security Pipeline Integration

## 🛡️ Overview

This document explains how CDK Nag security scanning has been integrated into the GitLab CI/CD pipeline to automatically detect infrastructure security issues.

## 🏗️ Pipeline Integration

### Security Stage Enhancement

The GitLab CI pipeline now includes two security jobs in the `security` stage:

1. **`security-scan`** - Code-level security scanning (Bandit, Safety)
2. **`cdk-nag-security`** - Infrastructure security scanning (CDK Nag)

### CDK Nag Job Configuration

```yaml
cdk-nag-security:
  stage: security
  image: node:20-alpine
  variables:
    CI: "true"  # Skips Docker bundling for faster analysis
  before_script:
    - # Install Python, CDK, and dependencies
  script:
    - python security_analysis_ci.py | tee cdk-nag-report.txt
  artifacts:
    - cdk-nag-report.txt
    - SECURITY_ANALYSIS_REPORT.md
```

## 🔍 Security Checks Performed

### AWS Solutions Checks
CDK Nag runs comprehensive security checks including:

- **S3 Security**: Encryption, public access, versioning
- **IAM Security**: Least privilege, policy validation
- **Lambda Security**: Runtime versions, timeout settings
- **DynamoDB Security**: Encryption, backup configuration
- **API Gateway Security**: Authentication, authorization
- **Network Security**: VPC configuration, security groups

### Compliance Standards
- AWS Well-Architected Security Pillar
- AWS Security Best Practices
- Industry security standards (SOC 2, ISO 27001)

## 🚀 Usage

### Automatic Execution
The security analysis runs automatically on:
- Merge requests
- Main branch commits
- Develop branch commits

### Manual Testing
Test the security pipeline locally:
```bash
./scripts/test_security_pipeline.sh
```

### Pipeline Behavior
- **✅ Success**: No security violations found - pipeline continues
- **❌ Failure**: Security violations detected - pipeline stops
- **⚠️ Warning**: Non-critical issues - pipeline continues with warnings

## 📊 Reports and Artifacts

### Generated Artifacts
1. **`cdk-nag-report.txt`** - Detailed security analysis output
2. **`SECURITY_ANALYSIS_REPORT.md`** - Comprehensive security report
3. **`cdk.out/`** - CDK synthesis output for review

### Viewing Results
- **GitLab UI**: Check the security stage job logs
- **Artifacts**: Download reports from the pipeline artifacts
- **Security Tab**: View security findings in GitLab's security dashboard

## 🔧 Configuration

### Environment Variables
- `CI=true` - Enables CI mode (skips Docker bundling)
- `AWS_DEFAULT_REGION` - AWS region for analysis
- `CDK_VERSION` - CDK CLI version to use

### Customization Options

#### Adding Custom Rules
```python
# In security_analysis_ci.py
from cdk_nag import NagSuppressions

# Suppress specific rules if needed (use sparingly)
NagSuppressions.add_stack_suppressions(
    stack, 
    [{"id": "AwsSolutions-S1", "reason": "Access logging not required for this use case"}]
)
```

#### Adjusting Severity Levels
```python
# Configure which violations should fail the pipeline
aws_solutions_checks = AwsSolutionsChecks(
    verbose=True,
    log_ignores=False  # Set to True to ignore suppressed rules
)
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. CDK Nag Installation Fails
```bash
# Solution: Update pip and retry
pip install --upgrade pip
pip install cdk-nag
```

#### 2. Memory Issues in CI
```yaml
# Add to job configuration
variables:
  NODE_OPTIONS: "--max-old-space-size=4096"
```

#### 3. Timeout Issues
```yaml
# Increase job timeout
timeout: 30m
```

### False Positives
If CDK Nag reports false positives:

1. **Review the finding** - Ensure it's actually a false positive
2. **Add suppression** - Use `NagSuppressions.add_*` methods
3. **Document reasoning** - Always provide clear justification
4. **Minimal suppressions** - Only suppress what's absolutely necessary

### Debugging Pipeline Failures
```bash
# Local debugging
export CI=true
python security_analysis_ci.py

# Check specific CDK construct
cdk synth --verbose
```

## 📈 Benefits

### Security Benefits
- **Early Detection**: Catch security issues before deployment
- **Automated Scanning**: No manual security reviews needed
- **Compliance**: Ensure adherence to security standards
- **Documentation**: Automatic security reports

### Development Benefits
- **Fast Feedback**: Quick security validation in CI
- **Consistent Standards**: Same security checks for all developers
- **Educational**: Learn security best practices through violations
- **Confidence**: Deploy with security assurance

## 🔄 Maintenance

### Regular Updates
- **CDK Nag**: Update to latest version monthly
- **Rules**: Review and update security rules quarterly
- **Suppressions**: Audit suppressions annually

### Monitoring
- Track security violation trends
- Monitor pipeline performance
- Review security reports regularly

## 📚 Additional Resources

- [CDK Nag Documentation](https://github.com/cdklabs/cdk-nag)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-learning/)
- [GitLab Security Features](https://docs.gitlab.com/ee/user/application_security/)

## 🎯 Next Steps

1. **Test Integration**: Run `./scripts/test_security_pipeline.sh`
2. **Commit Changes**: Push the security integration to GitLab
3. **Monitor Pipeline**: Watch the security stage in action
4. **Review Reports**: Check generated security artifacts
5. **Iterate**: Refine rules and suppressions as needed

---

**Security is everyone's responsibility!** 🛡️

This integration helps ensure that security is built into your infrastructure from the ground up, not bolted on as an afterthought.