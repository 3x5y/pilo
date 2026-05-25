#!/bin/sh
set -e

zfs create $TEST_REPLICA
pilo storage-snapshot t0

capture_status pilo storage-replica-seed

assert_command_fail
echo "$OUTPUT" | assert_grep 'cannot receive new filesystem stream'
