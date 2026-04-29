#!/bin/sh
set -e

# create dataset AFTER replication
system-snapshot t0
system-replicate

zfs create $TEST_ROOT/active/admin/newds
zfs snapshot $TEST_ROOT/active/admin/newds@t1

capture_status system-replication-verify

assert_command_fail expected missing dataset
echo "$OUTPUT" | assert_grep behind
