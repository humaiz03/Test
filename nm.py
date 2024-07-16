import boto3
import json
import datetime

def get_lambda_details(lambda_name):
    client = boto3.client('lambda')
    response = client.get_function(FunctionName=lambda_name)
    return response

def get_s3_buckets_accessed_by_lambda(lambda_name_or_arn):
    cloudtrail_client = boto3.client('cloudtrail')
    lambda_client = boto3.client('lambda')

    # Extract Lambda function name from ARN or name
    lambda_name = lambda_name_or_arn.split(':')[-1]

    # Get Lambda function details
    lambda_details = get_lambda_details(lambda_name)
    function_arn = lambda_details['Configuration']['FunctionArn']

    # Define time range for CloudTrail lookup (last 90 days)
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=90)

    # Query CloudTrail logs for S3 events initiated by the Lambda function
    lookup_attributes = [
        {
            'AttributeKey': 'EventSource',
            'AttributeValue': 's3.amazonaws.com'
        },
        {
            'AttributeKey': 'UserIdentityArn',
            'AttributeValue': function_arn
        }
    ]

    s3_buckets = set()

    # Pagination to get all events
    next_token = None
    while True:
        if next_token:
            response = cloudtrail_client.lookup_events(
                LookupAttributes=lookup_attributes,
                StartTime=start_time,
                EndTime=end_time,
                MaxResults=50,
                NextToken=next_token
            )
        else:
            response = cloudtrail_client.lookup_events(
                LookupAttributes=lookup_attributes,
                StartTime=start_time,
                EndTime=end_time,
                MaxResults=50
            )

        for event in response['Events']:
            event_details = json.loads(event['CloudTrailEvent'])
            event_name = event_details.get('eventName')
            if event_name in ['GetObject', 'PutObject', 'ListBucket', 'DeleteObject']:
                bucket_name = event_details.get('requestParameters', {}).get('bucketName')
                if bucket_name:
                    s3_buckets.add(bucket_name)

        next_token = response.get('NextToken')
        if not next_token:
            break

    return list(s3_buckets)

def find_associated_resources(lambda_name_or_arn):
    lambda_name = lambda_name_or_arn.split(':')[-1]
    lambda_details = get_lambda_details(lambda_name)
    associated_resources = {
        'Lambda': [lambda_details['Configuration']['FunctionArn']],
        'S3': get_s3_buckets_accessed_by_lambda(lambda_name_or_arn)
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