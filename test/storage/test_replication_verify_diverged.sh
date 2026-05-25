#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

# create unrelated snapshot on target
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status pilo storage-replication-verify

assert_command_fail expected divergence
echo "$OUTPUT" | assert_grep divergence
