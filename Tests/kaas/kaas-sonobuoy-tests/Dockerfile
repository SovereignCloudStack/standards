FROM golang:1.23

# Use build arguments to get the correct architecture
ARG TARGETARCH

# Install kubectl based on the architecture
#See https://github.com/kubernetes-sigs/kubespray/pull/10066
RUN apt-get update && apt-get install -y wget jq && \
    if [ "$TARGETARCH" = "amd64" ]; then \
        wget https://cdn.dl.k8s.io/release/v1.31.1/bin/linux/amd64/kubectl -O /usr/bin/kubectl; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        wget https://cdn.dl.k8s.io/release/v1.31.1/bin/linux/arm64/kubectl -O /usr/bin/kubectl; \
    else \
        echo "Unsupported architecture: $TARGETARCH" && exit 1; \
    fi && \
    chmod +x /usr/bin/kubectl

COPY ./scs_k8s_conformance_tests /src/scs_k8s_conformance_tests
WORKDIR /src
COPY go.* /src/
ENV CGO_ENABLED=0
RUN go mod download

#see: https://docs.docker.com/build/guide/mounts/
RUN --mount=type=cache,target=/root/.cache/go-build \
    go test -c -o custom.test ./...

CMD ["bash", "-c", "go tool test2json ./custom.test -test.v"]
