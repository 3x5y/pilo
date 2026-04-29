#!/bin/sh
set -e

system-snapshot t0

system-replicate-safe

capture_status system-replication-verify
echo "$OUTPUT" | assert_grep "^STATUS=OK"
