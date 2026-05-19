#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

# create rogue replica child
zfs create $TEST_REPLICA/rogue
zfs snapshot $TEST_REPLICA/rogue@evil

capture_status pilo replication-verify

assert_command_fail expected orphan divergence
echo "$OUTPUT" | assert_grep DIVERGED
