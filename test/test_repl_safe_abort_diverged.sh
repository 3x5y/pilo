#!/bin/sh
set -e

system-snapshot t0
system-replicate

# introduce corruption
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status system-replicate-safe

assert_command_fail expected safe replication to abort
echo "$OUTPUT" | assert_grep divergence
