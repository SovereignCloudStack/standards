#!/bin/sh

REGISTRY="ghcr.io/sovereigncloudstack/standars"
IMG="k8s-sonobuoy-example-python"

if [[ -v IMAGE_VERSION_TAG ]]
then 
  export TAG=$IMAGE_VERSION_TAG
else
  export TAG="dev"
fi

docker build . -t $REGISTRY/$IMG:$TAG
#docker push $REGISTRY/$IMG:$TAG
