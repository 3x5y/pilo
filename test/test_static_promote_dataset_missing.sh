#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

with_writable $PILE \
    mkdir -p /$PILE/out/filing/2099

with_writable $PILE \
    mv /$PILE/in/file.txt /$PILE/out/filing/2099/file.txt

# dataset does NOT exist
capture_status system-static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset does not exist"
