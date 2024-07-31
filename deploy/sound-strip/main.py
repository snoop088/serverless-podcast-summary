import json
import boto3
from pytubefix import YouTube

s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = "video-source-container"


def lambda_handler(event, context):
    # Define the YouTube URL
    yt = YouTube(event['body']['url'])

    # Filter to fetch only the audio stream
    audio = yt.streams.filter(only_audio=True).first()

    # Download the audio to the local temporary directory
    file = audio.download(output_path='/tmp', mp3=True)
    # convert it with AudioSegment
    s3_client.upload_file(file, bucket_name, f"{file.split('/')[-1]}")
    return {
        'statusCode': 200,
        'body': f'Hello from Lambda. Your file is {file}'
    }
