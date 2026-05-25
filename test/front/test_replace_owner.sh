#!/bin/sh
set -eu

mkfile old file.txt
capture_file file.txt
pilo content-ingest

echo new > "$TMP/new.txt"

pilo content-replace "$TMP/new.txt" in/file.txt

owner=$(stat -c %U "$PILO_PILE_PATH/in/file.txt")

[ "$owner" = "$PILO_USER" ] \
    || fail "ownership not enforced"
