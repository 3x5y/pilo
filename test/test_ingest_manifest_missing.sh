#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
# ensure no manifest exists
rm -f /$PILE/.manifest 2>/dev/null || true

system-ingest-pile

assert_file_exists /$PILE/.manifest
assert_manifest_valid /$PILE
