#!/bin/sh
set -e

# create child dataset
zfs create $TEST_ROOT/active/admin/sub

system-snapshot t0
system-replicate

# introduce rogue snapshot ONLY in child dataset
zfs snapshot $TEST_REPLICA/active/admin/sub@evil

capture_status system-replication-verify

assert_command_fail expected child divergence
echo "$OUTPUT" | assert_grep divergence
