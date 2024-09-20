FROM golang:1.23

# Install kubectl
# Note: Latest version may be found on:
# https://aur.archlinux.org/packages/kubectl-bin/
RUN wget https://storage.googleapis.com/kubernetes-release/release/v1.30.4/bin/linux/amd64/kubectl -O /usr/bin/kubectl && \
    chmod +x /usr/bin/kubectl && \
    apt-get update && \
    apt-get install -y jq

COPY . /src/
WORKDIR /src
COPY go.* /src/
ENV CGO_ENABLED=0
RUN go mod download

#see: https://docs.docker.com/build/guide/mounts/
RUN --mount=type=cache,target=/root/.cache/go-build \
    go test -c -o custom.test ./...

CMD ["bash", "-c", "go tool test2json ./custom.test -test.v"]
