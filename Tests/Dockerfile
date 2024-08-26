# syntax=docker/dockerfile:1

FROM python:3.10

WORKDIR /scs-compliance

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT ["./scs-compliance-check.py"]
CMD ["-h"]
