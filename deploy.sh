#!/bin/bash

# Define variables
S3_BUCKET=nick-gen-purpose
STACK_NAME=sound-manip

rm -rf deploy
mkdir deploy
cp -r template.yml sound-strip transcribe-summariser sound-transcriber ./deploy
cd deploy

# Package using AWS SAM
echo "Packaging the application using AWS SAM..."
sam package --template-file template.yml --output-template-file packaged.yml --s3-bucket $S3_BUCKET

# Deploy using AWS SAM
echo "Deploying the application to AWS..."
sam deploy --template-file packaged.yml --stack-name $STACK_NAME --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND

echo "Deployment complete. You can check the status of the stack in the AWS CloudFormation console."
