#!/bin/sh
set -eu

mkfile old file.txt
capture_file file.txt
pilo ingest-pile

echo new > "$TMP/new.txt"

pilo replace "$TMP/new.txt" in/file.txt

[ "$(zfs get -H -o value readonly $PILE)" = "on" ] \
    || fail "readonly not restored after write"
