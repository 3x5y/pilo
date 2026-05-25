#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
pilo content-ingest
# simulate re-upload
mkintake data $file
pilo content-ingest

# manifest still valid
assert_manifest_valid pile /$PILE

manifest="$PILO_ADMIN_PATH"/manifest/pile.manifest
# only one entry
count=$(grep -c " \./in/$file$" $manifest) \
    || fail "file not present in manifest"
[ "$count" -eq 1 ] || fail "duplicate manifest entries"
