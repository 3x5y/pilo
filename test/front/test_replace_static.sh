#!/bin/sh
set -eu

echo skipped
exit 0
mkfile old file.txt
capture_file file.txt
pilo ingest-pile

with_writable $PILE \
    mkdir -p "$PILO_PILE_PATH/out/collection"
with_writable $PILE \
    mv "$PILO_PILE_PATH/in/file.txt" \
       "$PILO_PILE_PATH/out/collection/file.txt"

pilo static-promote

echo new > "$TMP/new.txt"

pilo replace "$TMP/new.txt" collection/file.txt

grep -q new "$PILO_STATIC_PATH/collection/file.txt" \
    || fail "static replace failed"
