import json
import os
import urllib.parse
import boto3


s3_client = boto3.client('s3', region_name='us-east-1')
mediaconvert_client = boto3.client('mediaconvert')
output_bucket = 'sound-output-container'

def lambda_handler(event, context):
    # Get the S3 bucket and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding="utf-8")

    # Define the input and output paths
    input_s3_path = f"s3://{bucket_name}/{object_key}"
    output_key_prefix = object_key.rsplit('.', 1)[0]

    # Define the output location and filename
    output_s3_path = f"s3://{output_bucket}/{output_key_prefix}.mp3"
    print('input path', input_s3_path)
    print('output path', output_s3_path)
    try:
        # Create a MediaConvert job
        response = mediaconvert_client.create_job(
            Role=os.environ['MEDIA_CONVERT_ROLE'],
            Settings={
                "Inputs": [{
                    "FileInput": input_s3_path
                }],
                "OutputGroups": [{
                    "Name": "File Group",
                    "OutputGroupSettings": {
                        "Type": "FILE_GROUP_SETTINGS",
                        "FileGroupSettings": {
                            "Destination": output_s3_path
                        }
                    },
                    "Outputs": [{
                        "ContainerSettings": {
                            "Container": "MP3"
                        },
                        "AudioDescriptions": [{
                            "CodecSettings": {
                                "Codec": "MP3",
                                "Mp3Settings": {
                                    "Bitrate": 64000,
                                    "Channels": 2,
                                    "SampleRate": 44100
                                }
                            }
                        }]
                    }]
                }]
            }
        )

        job_id = response['Job']['Id']

        return {
            'statusCode': 200,
            'body': f'Successfully started MediaConvert job {job_id} for {object_key}'
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
