#!/bin/bash

read -p 'Enter tag for the image: ' imagetag

docker build -t lambda_extract -f Dockerfile-aws .


aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 156988614292.dkr.ecr.us-west-2.amazonaws.com

docker tag lambda_extract 156988614292.dkr.ecr.us-west-2.amazonaws.com/pcpr_extract:$imagetag
docker push 156988614292.dkr.ecr.us-west-2.amazonaws.com/pcpr_extract:$imagetag

echo "Pushed to ECR successfully! You will need to update the Lambda to use the new image."