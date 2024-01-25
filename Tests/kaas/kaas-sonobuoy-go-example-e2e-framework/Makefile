# Makefile
# This makefile is for development purpose

SHELL = /bin/bash
#SED ?= sed

DOCKERFILE="Dockerfile"
IMAGE_REGISTRY="ghcr.io/sovereigncloudstack/standards"
IMAGE_NAME="scsconformance"
#IMAGE_VERSION_TAG ="v0.1.2"

KIND_CLUSTER ="testcluster"

#PLUGIN_NAME="k8s-default-storage-class-plugin-go"
PLUGIN_NAME="plugin"
PLUGIN_FILE="${PLUGIN_NAME}.yaml"

#~ SONO_WAIT    = 1
#~ SONO_TIMEOUT = 60

KUBERNETES_SERVICE_HOST=127.0.0.1
KUBERNETES_SERVICE_PORT=34743


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
	@echo "[check-test-setup]"
	@kind version
	@docker version
	@sonobuoy version --short
	@go version


dev-setup: kind-init
	kind create cluster --name ${KIND_CLUSTER}


dev-build: container-init
	@echo "[build]"
	DOCKER_BUILDKIT=1 docker build . -f ${DOCKERFILE} -t ${SONOBUOY_IMAGE}
	kind load docker-image --name ${KIND_CLUSTER} ${SONOBUOY_IMAGE}


dev-go:
	@echo "[go]"
	@echo "[KubernetesService]   ${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}"
	@rm -rf ./build || true
	@mkdir ./build
	go test -c -o ./build ./...
#	go test -c -o ./build ./... --args --skip-labels="type=pod-list"
#	go tool test2json ./build -test.v


dev-run:
	@echo "[run-test]"
	@echo "sonobuoy run --plugin ${PLUGIN_FILE} --wait=${SONO_WAIT} --timeout=${SONO_TIMEOUT}"
#~ 	@sonobuoy run --plugin ${PLUGIN_FILE} --wait=${SONO_WAIT} --timeout=${SONO_TIMEOUT}
	@sonobuoy run --plugin ${PLUGIN_FILE} 
	@sonobuoy status


dev-result:
	@echo "[result]"
	#outfile=$(sonobuoy retrieve) && mkdir results && tar -xf ${outfile} -C results
	sonobuoy retrieve
	sonobuoy results *.tar.gz
	mkdir results
	tar -xf *.tar.gz -C results


dev-clean:
	@echo "[clean]"
	@sonobuoy delete --all --wait || true
	@sonobuoy status || true
	@rm -rf *.tar.gz || true
	@rm -rf results || true



dev-purge: kind-init dev-clean
	@echo "[purge]"
	kind delete cluster --name ${KIND_CLUSTER} || true
	docker rmi ${SONOBUOY_IMAGE} || true


PHONY: dev-prerequests dev-build dev-run dev-result dev-clean dev-clean dev-purge
