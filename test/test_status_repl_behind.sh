#!/bin/sh
set -e

# initial snapshot + replication
system-snapshot t0
system-replicate
# new snapshot, NOT replicated
system-snapshot t1

capture_status system-status replication

assert_command_fail expected replication drift
echo "$OUTPUT" | assert_grep replication
echo "$OUTPUT" | assert_grep t1
