#!/bin/sh
set -e

pilo snapshot t0

pilo replicate-safe

capture_status pilo replication-verify
echo "$OUTPUT" | assert_grep "^STATUS=OK"
