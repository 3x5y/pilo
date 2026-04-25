#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/test3.txt

echo original > $FILE

system-manifest-update

echo corruption > $FILE

capture_status system-manifest-verify

[ $STATUS -ne 0 ] || fail manifest-verify returned success
echo "$OUTPUT" | assert_grep FAILED
