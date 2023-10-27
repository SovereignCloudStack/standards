#!/usr/bin/env bash

IMAGE_REGISTRY=ghcr.io/sovereigncloudstack/standards
IMAGE_NAME=scsconformance

if [[ -v IMAGE_VERSION_TAG ]]
then 
  export TAG=$IMAGE_VERSION_TAG
else
  export TAG="dev"
fi

docker build . -t $IMAGE_REGISTRY/$IMAGE_NAME:$TAG
#docker push $IMAGE_REGISTRY/$IMAGE_NAME:$TAG
