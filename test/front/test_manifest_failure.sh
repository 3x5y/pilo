#!/bin/sh
set -e

file=test.txt
mkfile original $file
capture_file $file
pilo content-ingest
with_writable $PILE \
    sh -c "echo corruption > /$PILE/in/$file"

capture_status pilo manifest-verify

assert_command_fail manifest-verify returned success
echo "$OUTPUT" | assert_grep FAILED
