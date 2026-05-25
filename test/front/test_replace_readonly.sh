#!/bin/sh
set -eu

mkfile old file.txt
capture_file file.txt
pilo content-ingest

echo new > "$TMP/new.txt"

pilo content-replace "$TMP/new.txt" in/file.txt

[ "$(zfs get -H -o value readonly $PILE)" = "on" ] \
    || fail "readonly not restored after write"
