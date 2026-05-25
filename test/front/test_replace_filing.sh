#!/bin/sh
set -eu

echo skipped
exit 0
archive=filing/2025
mkfile old file.txt
capture_file file.txt
pilo content-ingest

with_writable $PILE \
    mkdir -p "$PILO_PILE_PATH/out/$archive"
with_writable $PILE \
    mv "$PILO_PILE_PATH/in/file.txt" \
       "$PILO_PILE_PATH/out/$archive/file.txt"

zfs create -p $STATIC/$archive
pilo static-promote

echo new > "$TMP/new.txt"

pilo content-replace "$TMP/new.txt" $archive/file.txt

grep -q new "$PILO_STATIC_PATH/$archive/file.txt" \
    || fail "static replace failed"
