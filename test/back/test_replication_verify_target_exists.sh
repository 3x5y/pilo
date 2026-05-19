#!/bin/sh
set -e

pilo snapshot t0
zfs create $TEST_REPLICA

capture_status pilo replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR: replica is uninitialized"
