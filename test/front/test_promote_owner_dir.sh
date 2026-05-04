#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

with_writable $PILE \
    mkdir "$PILO_PILE_PATH"/out/collection/dirx
with_writable $PILE \
    mv "$PILO_PILE_PATH"/in/file.txt \
       "$PILO_PILE_PATH"/out/collection/dirx/file.txt

pilo static-promote

assert_owner $PILO_USER "$PILO_STATIC_PATH"/collection/dirx
