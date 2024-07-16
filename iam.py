import boto3
import json

def get_lambda_details(lambda_name):
    client = boto3.client('lambda')
    response = client.get_function(FunctionName=lambda_name)
    return response

def get_iam_role_name(lambda_name):
    lambda_details = get_lambda_details(lambda_name)
    role_arn = lambda_details['Configuration']['Role']
    role_name = role_arn.split('/')[-1]
    return role_name

def get_s3_buckets_from_iam_role(role_name):
    iam_client = boto3.client('iam')
    
    # Get the IAM role details
    role_policies = iam_client.list_attached_role_policies(RoleName=role_name)
    
    buckets = set()
    
    for policy in role_policies['AttachedPolicies']:
        policy_arn = policy['PolicyArn']
        
        # Get the policy document
        policy_version = iam_client.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
        policy_document = iam_client.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=policy_version
        )['PolicyVersion']['Document']
        
        # Look for S3 bucket ARNs in the policy document
        for statement in policy_document['Statement']:
            if 'Action' in statement:
                actions = statement['Action']
                if isinstance(actions, str):
                    actions = [actions]
                for action in actions:
                    if 's3:' in action:
                        resources = statement.get('Resource', [])
                        if isinstance(resources, str):
                            resources = [resources]
                        for resource in resources:
                            if 'arn:aws:s3:::' in resource:
                                buckets.add(resource.split(':::')[1])
    
    return list(buckets)

def find_associated_resources(lambda_name_or_arn):
    lambda_name = lambda_name_or_arn.split(':')[-1]
    role_name = get_iam_role_name(lambda_name)
    associated_resources = {
        'Lambda': [lambda_name_or_arn],
        'S3': get_s3_buckets_from_iam_role(role_name)
    }
    return associated_resources

if __name__ == "__main__":
    lambda_name_or_arn = input("Enter the Lambda function name or ARN: ")
    resources = find_associated_resources(lambda_name_or_arn)
    print(f"Associated resources for Lambda {lambda_name_or_arn}:")
    for resource_type, resource_list in resources.items():
        print(f"{resource_type}:")
        for resource in resource_list:
            print(f"  - {resource}")