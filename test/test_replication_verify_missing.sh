#!/bin/sh
set -e

system-snapshot t0
system-replicate

system-snapshot t1

# simulate lost replication
zfs destroy $TEST_ROOT@t0

capture_status system-replication-verify

assert_command_fail expected broken continuity
echo "$OUTPUT" | assert_grep divergence
