#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

with_writable $PILE \
    mkdir -p "$PILO_PILE_PATH/out/collection"
with_writable $PILE \
    mv "$PILO_PILE_PATH/in/file.txt" \
       "$PILO_PILE_PATH/out/collection/file.txt"

pilo static-promote

script=$(printf "mv\tcollection/file.txt\tcollection/x.txt\n")
pilo rewrite "$script"

assert_manifest_valid static "$PILO_STATIC_PATH"
