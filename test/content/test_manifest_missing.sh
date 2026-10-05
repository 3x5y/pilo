#!/bin/sh
set -e

echo data > /$PILE/in/file.txt
create_pile_manifest
rm /$PILE/in/file.txt

capture_status pilo manifest-verify

assert_command_fail expected failure for missing file
echo "$OUTPUT" | assert_grep FAILED
