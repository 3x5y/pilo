#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
FILE=test_missing.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
system-manifest-update

with_dataset_writable $PILE rm /$PILE/$FILE

capture_status system-manifest-verify
assert_command_fail expected failure for missing file
echo "$OUTPUT" | assert_grep FAILED
