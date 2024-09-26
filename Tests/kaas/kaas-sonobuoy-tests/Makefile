# Makefile
# This makefile is for development purpose

###############################################################################
## Setup:  							                                                     ##
###############################################################################
SHELL = /bin/bash

DOCKERFILE="Dockerfile"
IMAGE_REGISTRY="ghcr.io/sovereigncloudstack/standards"
IMAGE_NAME="scs-kaas-conformance"

KIND_CLUSTER ="testcluster"

PLUGIN_NAME="scs-conformance-sonobuoy-plugin"
PLUGIN_FILE="${PLUGIN_NAME}.yaml"
KIND_CONFIG_FILE="kind_config.yaml"

SONO_WAIT= 30

###############################################################################
## Helpers:  							                                                   ##
###############################################################################

ifeq ($(IMAGE_VERSION_TAG),)
	export TAG=dev
else
	export TAG=${IMAGE_VERSION_TAG}
endif

SONOBUOY_IMAGE = "${IMAGE_REGISTRY}/${IMAGE_NAME}:${TAG}"

container-init:
	@echo ""
	@echo "[ContainerImageName]   ${SONOBUOY_IMAGE}"
	@echo "[SonobuoyPluginFile]   ${PLUGIN_FILE}"
	@echo ""


kind-init:
	@echo ""
	@echo "[KindCluster]   ${KIND_CLUSTER}"
	@echo ""

###############################################################################
## For develpoment usage:                                                    ##
###############################################################################

dev-prerequests:
	@kind version
	@docker version -f json | jq '.Client.Version'
	@sonobuoy version --short
	@yq --version
	@jq --version
	@go version
	@docker buildx version


dev-setup: kind-init
	kind create cluster --config ${KIND_CONFIG_FILE} --name ${KIND_CLUSTER}


dev-build: container-init
	@echo "[Building image...]"
	DOCKER_BUILDKIT=1 docker build . -f ${DOCKERFILE} -t ${SONOBUOY_IMAGE}
	kind load docker-image --name ${KIND_CLUSTER} ${SONOBUOY_IMAGE}


dev-run:
	@echo "[Running sonobuoy...]"
	@sonobuoy run -p ${PLUGIN_FILE} --wait=${SONO_WAIT}
	@sonobuoy status


dev-run-background:
	@echo "[Running sonobuoy in background...]"
	@sonobuoy run -p ${PLUGIN_FILE}
	@sonobuoy status


dev-result: dev-clean-result
	@echo "[Retrieve results...]"
	sonobuoy retrieve
	@echo "[Extracting results...]"
	mkdir results
	tar -xf *.tar.gz -C results
	cat results/plugins/scs-kaas-conformance/sonobuoy_results.yaml | yq
	cat results/plugins/scs-kaas-conformance/results/global/out.json | jq
	@echo "[Displaying results...]"
	sonobuoy results *.tar.gz


dev-rerun: dev-clean-sonobuoy dev-build dev-run dev-result


dev-clean-result:
	@rm -rf *.tar.gz || true
	@rm -rf results || true


dev-clean-sonobuoy: dev-clean-result
	@echo "[Cleanup sonobuoy environment from cluster...]"
	@sonobuoy delete --all --wait || true
	@sonobuoy status || true


dev-purge: kind-init dev-clean-sonobuoy
	@echo "[Purge everthing...]"
	@echo "[Deleting kind cluster...]"
	kind delete cluster --name ${KIND_CLUSTER} || true
	@echo "[Removing docker image...]"
	docker rmi ${SONOBUOY_IMAGE} || true
	@rm -rf ./build || true

PHONY: dev-prerequests dev-build dev-run dev-result dev-clean-sonobuoy dev-clean-result dev-purge dev-rerun dev-run-background

