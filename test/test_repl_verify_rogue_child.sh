#!/bin/sh
set -e

# create child dataset
zfs create $TEST_ROOT/active/admin/sub

pilo snapshot t0
pilo replicate

# introduce rogue snapshot ONLY in child dataset
zfs snapshot $TEST_REPLICA/active/admin/sub@evil

capture_status pilo replication-verify

assert_command_fail expected child divergence
echo "$OUTPUT" | assert_grep divergence
