#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
pilo-ingest-pile
# simulate re-upload
mkintake data $file
pilo-ingest-pile

# manifest still valid
assert_manifest_valid /$PILE

# only one entry
count=$(grep -c " \./in/$file$" /$PILE/.manifest) \
    || fail "file not present in manifest"
[ "$count" -eq 1 ] || fail "duplicate manifest entries"
