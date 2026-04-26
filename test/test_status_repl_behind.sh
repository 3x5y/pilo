#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly

# initial snapshot + replication
zfs snapshot -r $TEST_ROOT@t0
system-replicate $TEST_ROOT $TEST_REPLICA

capture_status system-status replication

# new snapshot, NOT replicated
zfs snapshot -r $TEST_ROOT@t1

capture_status system-status replication
assert_command_fail expected replication drift
echo "$OUTPUT" | assert_grep replication
echo "$OUTPUT" | assert_grep t1
