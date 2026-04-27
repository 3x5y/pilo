#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

with_writable $PILE \
    mkdir -p /$PILE/out/filing

with_writable $PILE \
    mv /$PILE/in/file.txt /$PILE/out/filing/file.txt

capture_status system-static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid filing structure"
