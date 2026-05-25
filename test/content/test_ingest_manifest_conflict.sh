#!/bin/sh
set -e

file=file.txt
canonical=/$PILE/in/$file
mkfile original $file
capture_file $file
pilo content-ingest
# conflicting intake
mkintake different $file

capture_status pilo content-ingest

assert_command_fail expected checksum conflict
echo "$OUTPUT" | assert_grep "capture verification failed"
# manifest still valid
assert_manifest_valid pile /$PILE
# canonical unchanged
assert_grep original < $canonical
