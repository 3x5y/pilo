#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo content-ingest

printf "mv\tin/file.txt\tout/collection/dirx/file.txt" \
    | pilo content-reorg

pilo content-promote

assert_owner $PILO_USER "$PILO_STATIC_PATH"/collection/dirx
