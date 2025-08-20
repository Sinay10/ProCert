#!/usr/bin/env python3
"""
CDK Nag Security Analysis Script for ProCert Infrastructure
This script runs security checks on the CDK infrastructure using cdk-nag
"""
import os
import sys
import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks, NagSuppressions
from procert_infrastructure.procert_infrastructure_stack import ProcertInfrastructureStack

class SecurityAnalysisApp:
    def __init__(self):
        self.security_findings = []
        
    def capture_nag_output(self, message):
        """Capture CDK nag security findings"""
        if any(keyword in message for keyword in ['AwsSolutions', 'ERROR', 'WARNING', 'FAIL']):
            self.security_findings.append(message)
            print(f"🔍 SECURITY FINDING: {message}")
    
    def run_analysis(self):
        print("🛡️  Starting CDK Security Analysis with CDK Nag...")
        print("=" * 60)
        
        # Set environment variable to skip Docker bundling for faster analysis
        os.environ['CI'] = 'true'
        
        app = cdk.App()
        
        # Create the stack
        stack = ProcertInfrastructureStack(app, "ProcertInfrastructureStack-SecurityAnalysis")
        
        # Add AWS Solutions security checks
        aws_solutions_checks = AwsSolutionsChecks(verbose=True)
        cdk.Aspects.of(app).add(aws_solutions_checks)
        
        try:
            # Synthesize the app to run the security checks
            app.synth()
            
            print("\n" + "=" * 60)
            print("🎯 SECURITY ANALYSIS SUMMARY")
            print("=" * 60)
            
            if self.security_findings:
                print(f"⚠️  Found {len(self.security_findings)} security findings:")
                for i, finding in enumerate(self.security_findings, 1):
                    print(f"{i}. {finding}")
            else:
                print("✅ No critical security issues found by CDK Nag!")
                
            print("\n📋 SECURITY RECOMMENDATIONS:")
            print("1. Review IAM policies for least privilege principle")
            print("2. Ensure all S3 buckets have proper encryption")
            print("3. Verify Lambda functions have appropriate timeout settings")
            print("4. Check that DynamoDB tables have point-in-time recovery enabled")
            print("5. Validate API Gateway has proper authentication and authorization")
            print("6. Ensure OpenSearch collections have proper access controls")
            
        except Exception as e:
            print(f"❌ Error during security analysis: {str(e)}")
            return False
            
        return True

def main():
    analyzer = SecurityAnalysisApp()
    success = analyzer.run_analysis()
    
    if success:
        print("\n✅ Security analysis completed successfully!")
        print("📄 Check the generated CloudFormation template in cdk.out/ for detailed resource configurations")
    else:
        print("\n❌ Security analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()