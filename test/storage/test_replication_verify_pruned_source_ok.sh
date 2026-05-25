#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot t1
pilo storage-replicate

# prune old source snapshot
clear_holds
zfs destroy $TEST_ROOT@t0

capture_status pilo storage-replication-verify

assert_command_ok expected continuity after source pruning
echo "$OUTPUT" | assert_grep "STATUS=OK"
