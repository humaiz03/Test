import boto3
import re

def get_lambda_details(lambda_name):
    client = boto3.client('lambda')
    response = client.get_function(FunctionName=lambda_name)
    return response

def get_s3_buckets_used_by_lambda(lambda_name):
    client = boto3.client('logs')
    log_group_name = f'/aws/lambda/{lambda_name}'
    
    response = client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=5
    )
    
    buckets = set()
    for log_stream in response['logStreams']:
        log_stream_name = log_stream['logStreamName']
        
        log_events_response = client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            limit=100
        )
        
        for event in log_events_response['events']:
            message = event['message']
            s3_buckets = re.findall(r'arn:aws:s3:::[\w\-]+', message)
            for bucket in s3_buckets:
                buckets.add(bucket.split(':::')[1])
    
    return list(buckets)

def find_associated_resources(lambda_name_or_arn):
    lambda_name = lambda_name_or_arn.split(':')[-1]
    lambda_details = get_lambda_details(lambda_name)
    associated_resources = {
        'Lambda': [lambda_details['Configuration']['FunctionArn']],
        'S3': get_s3_buckets_used_by_lambda(lambda_name)
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
