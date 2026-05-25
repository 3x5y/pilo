#!/bin/sh
set -eu

echo skipped
exit 0
mkfile data file.txt
capture_file file.txt
pilo content-ingest

with_writable $PILE \
    mkdir -p "$PILO_PILE_PATH/out/collection"
with_writable $PILE \
    mv "$PILO_PILE_PATH/in/file.txt" \
       "$PILO_PILE_PATH/out/collection/file.txt"

pilo content-promote

pilo rewrite "$(printf "mv\tcollection/file.txt\tcollection/renamed.txt\n")"

assert_file_exists "$PILO_STATIC_PATH/collection/renamed.txt"
assert_not_exists "$PILO_STATIC_PATH/collection/file.txt"
