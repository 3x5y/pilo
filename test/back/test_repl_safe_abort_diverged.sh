#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

# introduce corruption
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status pilo replicate-safe

assert_command_fail expected safe replication to abort
echo "$OUTPUT" | assert_grep divergence
