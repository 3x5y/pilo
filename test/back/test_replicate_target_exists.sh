#!/bin/sh
set -e

zfs create $TEST_REPLICA
pilo snapshot t0

capture_status pilo replica-seed

assert_command_fail
echo "$OUTPUT" | assert_grep 'cannot receive new filesystem stream'
