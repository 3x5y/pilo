#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly

# initial snapshot + replication
zfs snapshot $SRC@t0
system-replicate

capture_status system-status replication

# new snapshot, NOT replicated
zfs snapshot $SRC@t1

capture_status system-status replication
assert_command_fail expected replication drift
echo "$OUTPUT" | assert_grep replication
echo "$OUTPUT" | assert_grep t1
