import json
import os
import urllib.parse
import boto3

s3_client = boto3.client('s3', region_name='us-east-1')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
output_bucket = "transcribed-texts-container"



def lambda_handler(event, context):
    # Define the YouTube URL
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding="utf-8")
    input_text = "";

    if ".json" in object_key:
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpfull text summariser.\n \
                                              Please summarise the following text in up to 20 key takeaways. Keep \
                                              only the important points in the list and do not repeat yourself. \
                                             <|eot_id|><|start_header_id|>user <|end_header_id|>{text}\n \
                                             <|eot_id|><|start_header_id|>assistant <|end_header_id|>"
        transcript_obj = s3_client.get_object(Bucket=bucket_name, Key=object_key)
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
            s3_client.upload(output_bucket, output_file)

            return {
                'statusCode': 200,
                'body': f'Hello from Lambda. Summary is: {response_body}'
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
            'body': 'Hello from Lambda. Invalid file upload'
        }
