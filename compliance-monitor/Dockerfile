# syntax=docker/dockerfile:1
FROM python:3.10-alpine
WORKDIR /code
COPY . .
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps
EXPOSE 8080
CMD ["python3", "./monitor.py"]
