import json
import re
import os
import boto3
from pytubefix import YouTube

s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = "video-source-container"


def lambda_handler(event, context):
    # Define the YouTube URL
    yt = YouTube(event['body']['url'], use_oauth=True, allow_oauth_cache=True)

    # Filter to fetch only the audio stream
    audio = yt.streams.filter(only_audio=True).first()

    # Download the audio to the local temporary directory
    file = audio.download(output_path='/tmp', mp3=True)

    sanitized_file = re.sub(r'\s+', '-', file.strip())

    sanitized_file = re.sub(r'[^a-zA-Z0-9-_./]', '', sanitized_file)
    sanitized_file = re.sub(r'[-_]+', '-', sanitized_file)
    os.rename(file, sanitized_file)
    # convert it with AudioSegment
    s3_client.upload_file(sanitized_file, bucket_name, f"{sanitized_file.split('/')[-1]}")
    return {
        'statusCode': 200,
        'body': f'Hello from Lambda. Your file is {sanitized_file}'
    }
