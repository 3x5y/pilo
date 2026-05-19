#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

pilo snapshot t1
pilo replicate

# prune old source snapshot
zfs destroy $TEST_ROOT@t0

capture_status pilo replication-verify

assert_command_ok expected continuity after source pruning
echo "$OUTPUT" | assert_grep "STATUS=OK"
