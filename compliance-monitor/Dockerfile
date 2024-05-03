# syntax=docker/dockerfile:1
FROM python:3.10
RUN useradd -g users  -u 1001 -m -s /bin/bash runuser
USER 1001
WORKDIR /code
COPY requirements.txt requirements.txt
# for python:3.10-alpine
# RUN \
#  apk add --no-cache postgresql-libs && \
#  apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
#  python3 -m pip install -r requirements.txt --no-cache-dir && \
#  apk --purge del .build-deps
RUN python3 -m pip install -r requirements.txt --no-cache-dir
COPY . .
EXPOSE 8080
CMD ["python3", "./monitor.py"]
