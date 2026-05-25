#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
# ensure no manifest exists
manifest="$PILO_ADMIN_PATH"/manifest/pile.manifest
rm -f $manifest 2>/dev/null || true

pilo content-ingest

assert_file_exists $manifest
assert_manifest_valid pile /$PILE
