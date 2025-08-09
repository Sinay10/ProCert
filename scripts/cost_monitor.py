#!/usr/bin/env python3
"""
AWS Cost Monitor for ProCert Intern Project

This script helps monitor AWS costs to avoid unexpected charges
on your personal AWS account.
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_cost_and_usage(days=30):
    """Get cost and usage data for the last N days."""
    client = boto3.client('ce')  # Cost Explorer
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        return response
    except Exception as e:
        print(f"Error getting cost data: {e}")
        return None


def get_current_month_cost():
    """Get current month's cost."""
    client = boto3.client('ce')
    
    now = datetime.now()
    start_of_month = now.replace(day=1).date()
    end_date = now.date()
    
    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_of_month.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost']
        )
        return response
    except Exception as e:
        print(f"Error getting monthly cost: {e}")
        return None


def get_service_costs(days=7):
    """Get costs by AWS service for the last N days."""
    client = boto3.client('ce')
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        # Aggregate costs by service
        service_costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                if service in service_costs:
                    service_costs[service] += cost
                else:
                    service_costs[service] = cost
        
        return service_costs
    except Exception as e:
        print(f"Error getting service costs: {e}")
        return {}


def check_free_tier_usage():
    """Check free tier usage (simplified)."""
    print("🆓 Free Tier Reminders:")
    print("=" * 40)
    print("• Lambda: 1M requests/month + 400,000 GB-seconds")
    print("• DynamoDB: 25GB storage + 25 RCU/WCU")
    print("• S3: 5GB storage + 20,000 GET requests")
    print("• API Gateway: 1M requests/month")
    print("• CloudWatch: 10 custom metrics + 5GB logs")
    print("\n💡 Tip: Monitor usage in AWS Console → Billing → Free Tier")


def main():
    """Main function to display cost information."""
    print("💰 ProCert AWS Cost Monitor")
    print("=" * 50)
    
    # Current month cost
    print("\n📅 Current Month Cost:")
    monthly_data = get_current_month_cost()
    if monthly_data and monthly_data['ResultsByTime']:
        total_cost = float(monthly_data['ResultsByTime'][0]['Total']['BlendedCost']['Amount'])
        print(f"   Total: ${total_cost:.2f}")
        
        if total_cost > 200:
            print("   🚨 ALERT: Cost is above $200!")
        elif total_cost > 100:
            print("   ⚠️  WARNING: Cost is above $100")
        elif total_cost > 50:
            print("   ⚡ NOTICE: Cost is above $50")
        else:
            print("   ✅ Cost is within reasonable limits")
    else:
        print("   Unable to retrieve monthly cost data")
    
    # Service breakdown
    print("\n🔧 Cost by Service (Last 7 days):")
    service_costs = get_service_costs(7)
    if service_costs:
        sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
        for service, cost in sorted_services[:10]:  # Top 10 services
            if cost > 0.01:  # Only show costs > 1 cent
                print(f"   {service}: ${cost:.2f}")
    else:
        print("   No service cost data available")
    
    # Free tier info
    print("\n")
    check_free_tier_usage()
    
    # Cost optimization tips
    print("\n💡 Cost Optimization Tips:")
    print("=" * 40)
    print("• Monitor OpenSearch instance size (biggest cost driver)")
    print("• Use appropriate instance types for your workload")
    print("• Clean up old CloudWatch log groups regularly")
    print("• Delete unused S3 objects and incomplete uploads")
    print("• Consider reserved instances for long-running resources")
    print("• Use 'cdk destroy' only when completely done with development")
    
    # Resource management
    print("\n🧹 Resource Management Commands:")
    print("=" * 40)
    print("# Check current resources:")
    print("aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE")
    print("")
    print("# Destroy CDK stack when project is complete:")
    print("cdk destroy --all")
    print("")
    print("# List S3 buckets:")
    print("aws s3 ls")
    print("")
    print("# Delete S3 bucket contents:")
    print("aws s3 rm s3://bucket-name --recursive")
    print("")
    print("# List Lambda functions:")
    print("aws lambda list-functions --query 'Functions[].FunctionName'")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCost monitoring interrupted by user")
    except Exception as e:
        print(f"\nError running cost monitor: {e}")
        print("Make sure you have AWS credentials configured and Cost Explorer enabled")