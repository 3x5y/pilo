#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
FILE=bad.txt

echo x > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

# deliberately DO NOT create dataset
with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/filing/2099
capture_status system-static-promote

assert_command_fail "accepted non-existent dataset"
echo "$OUTPUT" | assert_grep "dataset does not exist"
