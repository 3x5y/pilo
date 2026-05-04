#!/bin/sh
set -e

file=bad.txt
mkfile data $file
capture_file $file
pilo ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/filing/$file

capture_status pilo static-promote

assert_command_fail accepted invalid structure
echo "$OUTPUT" | assert_grep "invalid filing structure"
