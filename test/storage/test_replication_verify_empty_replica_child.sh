#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

zfs create $TEST_ROOT/admin/newds
zfs snapshot $TEST_ROOT/admin/newds@t1

zfs create $TEST_REPLICA/admin/newds

capture_status pilo storage-replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep DIVERGED
