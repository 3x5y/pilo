#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
file=file.txt
canonical=/$PILE/in/$file

mkfile original $file
capture_file $file
system-ingest-pile

# conflicting intake
mkintake different $file

capture_status system-ingest-pile

assert_command_fail expected checksum conflict
echo "$OUTPUT" | assert_grep "collision"

# manifest still valid
assert_manifest_valid /$PILE

# canonical unchanged
assert_grep original < $canonical
