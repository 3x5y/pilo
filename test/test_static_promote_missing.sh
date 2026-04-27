#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection
system-static-promote

# second promotion attempt (no re-ingest)
capture_status system-static-promote

assert_command_fail expected missing source failure
echo "$OUTPUT" | assert_grep "/out/ directory empty"
