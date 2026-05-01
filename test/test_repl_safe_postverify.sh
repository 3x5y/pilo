#!/bin/sh
set -e

pilo snapshot t0
pilo replicate

pilo snapshot t1

pilo replicate-safe >/dev/null

capture_status pilo replication-verify
assert_command_ok expected system to be consistent after safe replication
echo "$OUTPUT" | assert_grep "^STATUS=OK"
