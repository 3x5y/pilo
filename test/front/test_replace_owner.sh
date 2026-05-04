#!/bin/sh
set -eu

mkfile old file.txt
capture_file file.txt
pilo ingest-pile

echo new > "$TMP/new.txt"

pilo replace "$TMP/new.txt" in/file.txt

owner=$(stat -c %U "$PILO_PILE_PATH/in/file.txt")

[ "$owner" = "$PILO_USER" ] \
    || fail "ownership not enforced"
