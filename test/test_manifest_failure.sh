#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=test.txt

echo original > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
system-manifest-update

echo corruption > $PILE/$FILE

capture_status system-manifest-verify
[ $STATUS -ne 0 ] || fail manifest-verify returned success
echo "$OUTPUT" | assert_grep FAILED
