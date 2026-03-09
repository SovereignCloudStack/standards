#!/usr/bin/env bash 
exec dockerize -template /etc/postfix/main.cf.tmpl:/etc/postfix/main.cf  postfix start-fg
