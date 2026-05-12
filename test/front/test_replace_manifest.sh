#!/bin/sh
set -eu

mkfile old file.txt
capture_file file.txt
pilo ingest-pile

echo new > "$TMP/new.txt"

pilo replace "$TMP/new.txt" in/file.txt

assert_manifest_valid pile "$PILO_PILE_PATH"
