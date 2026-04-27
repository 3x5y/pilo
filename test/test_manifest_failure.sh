#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
FILE=test.txt

echo original > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
system-manifest-update

with_writable $PILE \
    sh -c "echo corruption > /$PILE/in/$FILE"

capture_status system-manifest-verify
assert_command_fail manifest-verify returned success
echo "$OUTPUT" | assert_grep FAILED
