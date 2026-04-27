#!/bin/sh
set -e

FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
system-static-promote $FILE collection

# second promotion attempt (no re-ingest)
capture_status system-static-promote $FILE collection

assert_command_fail expected missing source failure
echo "$OUTPUT" | assert_grep "source file missing"
