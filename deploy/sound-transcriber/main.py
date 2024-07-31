import json
import os
import uuid
import urllib.parse
import boto3

s3_client = boto3.client('s3', region_name='us-east-1')
transcription_client = boto3.client('transcribe', region_name='us-east-1')
output_bucket = "sound-transcribed-output"
output_path = "jobs"


def lambda_handler(event, context):
    # Define the YouTube URL
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding="utf-8")

    s3_path = f"s3://{bucket_name}/{object_key}"

    transcription_job_name = f"transcribe-job-{uuid.uuid4()}"
    response = transcription_client.start_transcription_job(
        TranscriptionJobName=transcription_job_name,
        LanguageCode='en-US',
        MediaFormat='mp3',
        OutputBucketName=output_bucket,
        # OutputKey=f"{output_path}/",
        Media={
            'MediaFileUri': s3_path
        }
    )
    job_status = response['TranscriptionJob']['TranscriptionJobStatus']
    return {
        'statusCode': 200,
        'body': f'Hello from Lambda. Your file is {job_status}'
    }
