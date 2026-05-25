#!/bin/sh
set -eu

mkfile old file.txt
capture_file file.txt
pilo content-ingest

echo new > "$TMP/new.txt"

pilo content-replace "$TMP/new.txt" in/file.txt

grep -q new "$PILO_PILE_PATH/in/file.txt" \
    || fail "file not replaced"
