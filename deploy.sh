#!/bin/bash

# Define variables
S3_BUCKET=nick-gen-purpose
STACK_NAME=sound-manip
# Default to production if no type is specified
ENV_TYPE=${1:-prod}
# Conditionally load the environment file based on the type
if [ "$ENV_TYPE" == "dev" ]; then
    ENV_FILE=".dev.env"
elif [ "$ENV_TYPE" == "prod" ]; then
    ENV_FILE=".env"
else
    echo "Unknown type: $ENV_TYPE"
    exit 1
fi

# Load the environment variables
if [ -f $ENV_FILE ]; then
    export $(grep -v '^#' $ENV_FILE | xargs)
    echo "Loaded environment variables from $ENV_FILE"
else
    echo "Environment file $ENV_FILE not found!"
    exit 1
fi

export $(grep -v '^#' .env | xargs)
rm -rf deploy
mkdir deploy
cp -r template.yml sound-strip transcribe-summariser sound-transcriber ./deploy
cd deploy

# Package using AWS SAM
echo "Packaging the application using AWS SAM..."
sam package --template-file template.yml --output-template-file packaged.yml --s3-bucket $S3_BUCKET

# Deploy using AWS SAM
echo "Deploying the application to AWS..."
sam deploy --template-file packaged.yml --stack-name $STACK_NAME --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --parameter-overrides AppsyncApiId=$APPSYNC_API_ID AmplifyFunctionName=$AMPLIFY_FUNCTION_NAME AppsyncApiUrl=$APPSYNC_API_URL

echo "Deployment complete. You can check the status of the stack in the AWS CloudFormation console."
