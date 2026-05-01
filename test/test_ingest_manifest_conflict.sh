#!/bin/sh
set -e

file=file.txt
canonical=/$PILE/in/$file
mkfile original $file
capture_file $file
pilo ingest-pile
# conflicting intake
mkintake different $file

capture_status pilo ingest-pile

assert_command_fail expected checksum conflict
echo "$OUTPUT" | assert_grep "collision"
# manifest still valid
assert_manifest_valid /$PILE
# canonical unchanged
assert_grep original < $canonical
