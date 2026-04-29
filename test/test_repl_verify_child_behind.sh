#!/bin/sh
set -e

zfs create $TEST_ROOT/active/admin/sub

system-snapshot t0
system-replicate

# new snapshot ONLY on child dataset
zfs snapshot $TEST_ROOT/active/admin/sub@t1

capture_status system-replication-verify

assert_command_fail expected child behind
echo "$OUTPUT" | assert_grep behind
