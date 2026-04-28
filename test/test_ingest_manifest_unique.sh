#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
system-ingest-pile
# simulate re-upload
mkintake data $file
system-ingest-pile

# manifest still valid
assert_manifest_valid /$PILE

# only one entry
COUNT=$(grep -c " \./in/$file$" /$PILE/.manifest) \
    || fail "file not present in manifest"
[ "$COUNT" -eq 1 ] || fail "duplicate manifest entries"
