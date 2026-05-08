#!/bin/sh
set -e

# initial snapshot + replication
pilo snapshot t0
pilo replicate
# new snapshot, NOT replicated
pilo snapshot t1

capture_status pilo status replication

assert_command_fail expected replication drift
echo "$OUTPUT" | assert_grep "replication: latest=t1"
