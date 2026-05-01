#!/bin/sh
set -e

pilo-snapshot t0
pilo-replicate

# create unrelated snapshot on target
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status pilo-replication-verify

assert_command_fail expected divergence
echo "$OUTPUT" | assert_grep divergence
