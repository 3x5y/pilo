#!/bin/sh
set -e

system-snapshot t0
system-replicate

# create unrelated snapshot on target
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status system-replication-verify

assert_command_fail expected divergence
echo "$OUTPUT" | assert_grep divergence
