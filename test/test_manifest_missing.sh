#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/test_missing.txt

echo data > $FILE

system-manifest-update

rm $FILE

capture_status system-manifest-verify

[ $STATUS -ne 0 ] || fail expected failure for missing file
echo "$OUTPUT" | assert_grep FAILED
