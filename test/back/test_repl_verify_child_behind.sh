#!/bin/sh
set -e

zfs create $TEST_ROOT/active/admin/sub

pilo snapshot t0
pilo replicate

# new snapshot ONLY on child dataset
zfs snapshot $TEST_ROOT/active/admin/sub@t1

capture_status pilo replication-verify

assert_command_fail expected child behind
echo "$OUTPUT" | assert_grep BEHIND
