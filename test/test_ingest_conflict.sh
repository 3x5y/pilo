#!/bin/sh
set -e

FILE=file.txt
INTAKE=/tank/data/active/pile-intake/$FILE
CANONICAL=/tank/data/active/pile-readonly/$FILE

echo original > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

# conflicting re-upload
echo different > $INTAKE

capture_status system-ingest-pile

assert_command_fail expected conflict rejection
echo "$OUTPUT" | assert_grep "ERROR"

# canonical must remain unchanged
assert_grep original < $CANONICAL

# intake should still contain the conflicting file (not silently deleted)
assert_file_exists $INTAKE
