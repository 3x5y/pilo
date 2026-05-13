#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

printf "mv\tin/file.txt\tout/collection/file.txt" \
    | pilo rewrite

pilo static-promote

assert_owner $PILO_USER "$PILO_STATIC_PATH"/collection/file.txt
