#!/bin/sh
set -e

file=test.txt
echo original > /$PILE/in/$file
create_pile_manifest
echo corruption > /$PILE/in/$file

capture_status pilo manifest-verify

assert_command_fail manifest-verify returned success
echo "$OUTPUT" | assert_grep FAILED
