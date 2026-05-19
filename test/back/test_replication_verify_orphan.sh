#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

zfs create $TEST_REPLICA/orphan
zfs snapshot $TEST_REPLICA/orphan@evil

capture_status pilo replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep orphan
