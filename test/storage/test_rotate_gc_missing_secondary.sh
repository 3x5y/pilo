#!/bin/sh
set -e

zfs destroy -r $REPLICA_ROOT 2>/dev/null || true

capture_status pilo storage-rotate-gc
assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR"
