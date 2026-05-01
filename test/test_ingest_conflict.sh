#!/bin/sh
set -e

file=file.txt
canonical=/$PILE/in/$file

mkfile original $file
capture_file $file
pilo-ingest-pile

# conflicting re-upload
mkintake different $file

capture_status pilo-ingest-pile

assert_command_fail expected conflict rejection
echo "$OUTPUT" | assert_grep "ERROR"

# canonical must remain unchanged
assert_grep original < $canonical

# intake should still contain the conflicting file (not silently deleted)
assert_file_exists /$INTAKE/$file
