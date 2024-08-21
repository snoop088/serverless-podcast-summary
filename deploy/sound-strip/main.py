import re
import os
import boto3
import yt_dlp
from pytubefix import YouTube

s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = "video-source-container"
cached_token_key = 'cached_token/tokens.json'
token_cache_dir = '/tmp/pytubefix_cache'
token_cache_path = os.path.join(token_cache_dir, 'tokens.json')


def dl_with_dlp(url):
    ydl_opts = {
        'format': 'bestaudio',  # Select the best audio quality available
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
            'preferredcodec': 'mp3',  # Convert audio to mp3 format
            # Quality of the mp3 audio (bitrate in kbps)
            'preferredquality': '96',
        }],
        'outtmpl': '/tmp/%(title)s.%(ext)s',  # Output file name template
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        downloaded_filename = ydl.prepare_filename(info_dict)

    file = downloaded_filename.split('/')[-1].split('.')[0] + '.mp3'
    return file


def prepare_token():
    if not os.path.exists(token_cache_dir):
        os.makedirs(token_cache_dir)
    if not os.path.exists(token_cache_path):
        try:
            s3_client.download_file(
                bucket_name, cached_token_key, token_cache_path)
            print(f"Downloaded tokens.json from S3 to {token_cache_path}")
        except Exception as e:
            print(f"Error downloading tokens.json from S3: {e}")
            # Handle the error as needed, possibly re-throw or exit
    else:
        print(f"Token file already exists in {token_cache_path}")


def lambda_handler(event, context):
    # Define the YouTube URL
    prepare_token()
    yt = YouTube(event['body']['url'], use_oauth=True,
                 allow_oauth_cache=True, token_file=token_cache_path)

    audio = yt.streams.filter(only_audio=True).first()

    # # Download the audio to the local temporary directory
    file = audio.download(output_path='/tmp', mp3=True)

    sanitized_file = re.sub(r'\s+', '-', file.strip())

    sanitized_file = re.sub(r'[^a-zA-Z0-9-_./]', '', sanitized_file)
    sanitized_file = re.sub(r'[-_]+', '-', sanitized_file)
    os.rename(file, sanitized_file)
    # convert it with AudioSegment
    s3_client.upload_file(sanitized_file, bucket_name,
                          str(sanitized_file.split('/')[-1]))
    return {
        'statusCode': 200,
        'body': f'Hello from Lambda. Your file is {sanitized_file}'
    }
