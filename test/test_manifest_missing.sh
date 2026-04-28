#!/bin/sh
set -e

file=test_missing.txt
mkfile data $file
capture_file $file
system-ingest-pile
system-manifest-update
with_writable $PILE \
    rm /$PILE/in/$file

capture_status system-manifest-verify

assert_command_fail expected failure for missing file
echo "$OUTPUT" | assert_grep FAILED
