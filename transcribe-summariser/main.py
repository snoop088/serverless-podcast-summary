import json
import os
import urllib.parse
import boto3
import uuid
from datetime import datetime
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.httpsession import URLLib3Session
s3_client = boto3.client('s3', region_name='us-east-1')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
output_bucket = "transcribed-texts-container"


def update_table_with_appsync(title, generation):
    appsync_url = os.getenv('APPSYNC_API_URL')
    new_item = {
        'id': str(uuid.uuid4()),
        'owner': '744874a8-e0d1-70c0-2feb-945cb1bde96e',
        'createdAt': datetime.now().isoformat() + 'Z',
        'updatedAt': datetime.now().isoformat() + 'Z',
        'title': 'Summary of: ' + title,
        'content': generation,
        'author': 'AI'
    }
    mutation = """
    mutation MyMutation($input: CreateNewsInput!) {
      createNews(input: $input) {
        title
        createdAt
        content
        id
        author
        owner
        updatedAt
      }
    }
    """
    variables = {
        "input": {
            "title": new_item['title'],
            "author": new_item['author'],
            "content": new_item['content'],
            "id": new_item["id"]
        }
    }

    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = session.region_name

    # Create the request object
    request = AWSRequest(
        method="POST",
        url=appsync_url,
        data=json.dumps({"query": mutation, "variables": variables}),
        headers={"Content-Type": "application/json"}
    )
    SigV4Auth(credentials, "appsync", region).add_auth(request)

    # Send the signed request using a botocore endpoint
    http_session = URLLib3Session()
    response = http_session.send(request.prepare())
    return json.loads(response.content)
    # return response['data']['createNews']['id']


def lambda_handler(event, context):
    # Define the YouTube URL
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding="utf-8")
    input_text = ""

    if ".json" in object_key:
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpfull text summariser.\n \
                                              Please summarise the following text in up to 20 key takeaways. Keep \
                                              only the important points in the list and do not repeat yourself. \
                                             <|eot_id|><|start_header_id|>user <|end_header_id|>{text}\n \
                                             <|eot_id|><|start_header_id|>assistant <|end_header_id|>"
        transcript_obj = s3_client.get_object(
            Bucket=bucket_name, Key=object_key)
        transcript_stream = transcript_obj['Body'].read().decode('utf-8')

        transcript_json = json.loads(transcript_stream)
        if transcript_json is not None:
            text = transcript_json['results']['transcripts'][0]['transcript']
            input_text = prompt.format(text=text)
            kwargs = {
                "modelId": "meta.llama3-8b-instruct-v1:0",
                "contentType": "application/json",
                "accept": "*/*",
                "body": json.dumps(
                    {
                        "prompt": input_text,
                        "max_gen_len": 512,
                        "top_p": 0.85
                    }
                )
            }

            response = bedrock_runtime.invoke_model(**kwargs)
            response_body = json.loads(response['body'].read().decode('utf-8'))
            response_body = response_body['generation']
            output_file = f"/tmp/{object_key.split('.')[0]}.txt"
            with open(output_file, 'w') as f:
                f.write(response_body)
            s3_client.upload_file(output_file, output_bucket,
                                  str(output_file.split('/')[-1]))

            result = update_table_with_appsync(
                object_key, response_body)
            return {
                'statusCode': 200,
                'body': f'Hello from Lambda. This is the added item: {json.dumps(result)}'
            }
        else:
            return {
                'statusCode': 500,
                'body': 'Error transcribing the document'
            }
    # s3_path = f"s3://{bucket_name}/{output_path}/{object_key}"

    else:
        return {
            'statusCode': 500,
            'body': 'Error. Invalid file upload'
        }
