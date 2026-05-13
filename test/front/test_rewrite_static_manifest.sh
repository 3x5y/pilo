#!/bin/sh
set -eu

echo skipped
exit 0
mkfile data file.txt
capture_file file.txt
pilo ingest-pile

with_writable $PILE \
    mkdir -p "$PILO_PILE_PATH/out/collection"
with_writable $PILE \
    mv "$PILO_PILE_PATH/in/file.txt" \
       "$PILO_PILE_PATH/out/collection/file.txt"

pilo static-promote

printf "mv\tcollection/file.txt\tcollection/x.txt" \
    | pilo rewrite

assert_manifest_valid collection "$PILO_STATIC_PATH"/collection
