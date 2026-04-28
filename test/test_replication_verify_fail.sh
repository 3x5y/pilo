#!/bin/sh
set -e

system-snapshot t0
system-replicate

system-snapshot t1

# ORIGINAL, BROKEN
# simulate lost replication
# (destroy target snapshot so chain breaks)
#zfs destroy $TEST_REPLICA@t0
# AGENT SUGGESTED FIX
# create a rogue snapshot on target
#zfs snapshot $TEST_REPLICA/active@diverged
# MY FIX
zfs destroy $TEST_ROOT@t0

capture_status system-replication-verify

assert_command_fail expected broken continuity
echo "$OUTPUT" | assert_grep divergence
