#!/bin/sh
set -e

pilo snapshot t0
pilo replicate

pilo snapshot t1

# simulate lost replication
zfs destroy $TEST_ROOT@t0

capture_status pilo replication-verify

assert_command_fail expected broken continuity
echo "$OUTPUT" | assert_grep divergence
