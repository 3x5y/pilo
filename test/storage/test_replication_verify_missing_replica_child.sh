#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

zfs create $TEST_ROOT/active/admin/newds
zfs snapshot $TEST_ROOT/active/admin/newds@t1

capture_status pilo storage-replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep BEHIND
echo "$OUTPUT" | assert_grep missing
