#!/bin/sh
set -e

# initial snapshot + replication
pilo storage-snapshot t0
pilo storage-replica-seed
# new snapshot, NOT replicated
pilo storage-snapshot t1

capture_status pilo status replication

assert_command_fail expected replication drift
echo "$OUTPUT" | assert_grep "replication.behind"
