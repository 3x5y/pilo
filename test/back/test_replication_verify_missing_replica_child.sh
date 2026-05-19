#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

zfs create $TEST_ROOT/active/admin/newds
zfs snapshot $TEST_ROOT/active/admin/newds@t1

capture_status pilo replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep BEHIND
echo "$OUTPUT" | assert_grep missing
