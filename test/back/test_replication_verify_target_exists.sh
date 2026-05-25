#!/bin/sh
set -e

pilo storage-snapshot t0
zfs create $TEST_REPLICA

capture_status pilo storage-replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR: replica is uninitialized"
