#!/bin/sh
set -e

mkintake good foo/file.txt
system-ingest-pile
# conflicting re-upload
mkintake bad foo/file.txt

capture_status system-ingest-pile

assert_command_fail
echo "$OUTPUT" | assert_grep ERROR

assert_grep good < /$PILE/in/foo/file.txt
assert_file_exists /$INTAKE/foo/file.txt
