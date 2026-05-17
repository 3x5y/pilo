#!/bin/sh
set -e

pilo snapshot t0

capture_status pilo replicate-safe

#capture_status pilo replication-verify
assert_command_fail
echo "$OUTPUT"
echo "$OUTPUT" | assert_grep "^ERROR: missing required dataset"
