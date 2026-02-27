# syntax=docker/dockerfile:1

FROM python:3.10

WORKDIR /scs-compliance

ARG SONOBUOY_VERSION=0.57.3
ARG TARGETOS
ARG TARGETARCH

RUN set -eux; \
    wget -qO- https://github.com/vmware-tanzu/sonobuoy/releases/download/v$SONOBUOY_VERSION/sonobuoy_${SONOBUOY_VERSION}_${TARGETOS}_${TARGETARCH}.tar.gz \
      | tar -xz -C /usr/local/bin; \
    chmod +x /usr/local/bin/sonobuoy

COPY requirements.txt requirements.txt
COPY iaas/requirements.txt iaas-requirements.txt
COPY kaas/requirements.txt kaas-requirements.txt
RUN pip3 install -r requirements.txt -r iaas-requirements.txt -r kaas-requirements.txt

COPY . .

ENTRYPOINT ["./scs-compliance-check.py"]
CMD ["-h"]
