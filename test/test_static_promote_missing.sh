#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/
system-static-promote

# second promotion attempt (no re-ingest)
capture_status system-static-promote

assert_command_fail expected missing source failure
echo "$OUTPUT" | assert_grep "/out/ directory empty"
