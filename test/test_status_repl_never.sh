#!/bin/sh
set -e

zfs snapshot -r $TEST_ROOT@t0

capture_status system-status replication
assert_command_fail expected replication warning
echo "$OUTPUT" | assert_grep replication
