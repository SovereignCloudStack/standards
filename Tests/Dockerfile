# syntax=docker/dockerfile:1

FROM python:3.10

WORKDIR /scs-compliance

COPY requirements.txt requirements.txt
COPY iaas/requirements.txt iaas-requirements.txt
COPY kaas/requirements.txt kaas-requirements.txt
RUN pip3 install -r requirements.txt -r iaas-requirements.txt -r kaas-requirements.txt

COPY . .

ENTRYPOINT ["./scs-compliance-check.py"]
CMD ["-h"]
