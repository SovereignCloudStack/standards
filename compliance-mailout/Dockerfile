FROM alpine:edge
# install packages
RUN apk update --no-cache \
    && apk add --no-cache --update postfix bash openssl tini \
    && apk add --no-cache --upgrade musl musl-utils \
    && apk add  dockerize  --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/ \
    &&  (rm "/tmp/"* 2>/dev/null || true) && (rm -rf /var/cache/apk/* 2>/dev/null || true)

RUN  openssl genrsa -des3 -passout pass:x -out /etc/ssl/private/mailout.pass.key 4096 \
     && openssl rsa -passin pass:x -in etc/ssl/private/mailout.pass.key \
     -out /etc/ssl/private/mailout.key  \
     &&  openssl req -new -key /etc/ssl/private/mailout.key -out /etc/ssl/private/mailout.csr \
     -subj "/C=DE/ST=Berlin/L=Berlin/O=OrgName/OU=Standards/CN=sovereigncloudstack.org" \
     && openssl x509 -req -days 3650 -in /etc/ssl/private/mailout.csr -signkey /etc/ssl/private/mailout.key \
     -out /etc/ssl/certs/mailout.crt \
     && rm /etc/ssl/private/mailout.pass.key

COPY main.cf /etc/postfix/main.cf.tmpl
COPY relay_map /etc/postfix/relay_map
COPY security /etc/postfix/security
RUN postmap /etc/postfix/security
RUN postmap /etc/postfix/relay_map
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
RUN rm /etc/postfix/security
RUN rm /etc/postfix/relay_map

EXPOSE 25
STOPSIGNAL SIGKILL

ENTRYPOINT ["/sbin/tini", "--"]
CMD  ["/entrypoint.sh"]