#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

# missing dataset
zfs create $TEST_ROOT/active/admin/newds
zfs snapshot $TEST_ROOT/active/admin/newds@t1

capture_status pilo replication-verify
assert_command_fail
echo "$OUTPUT" | assert_grep BEHIND

# child drift
zfs create $TEST_ROOT/active/admin/sub
zfs snapshot $TEST_ROOT/active/admin/sub@t2

capture_status pilo replication-verify
assert_command_fail
echo "$OUTPUT" | assert_grep BEHIND

# rogue snapshot on target
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status pilo replication-verify
assert_command_fail
echo "$OUTPUT" | assert_grep DIVERGED
