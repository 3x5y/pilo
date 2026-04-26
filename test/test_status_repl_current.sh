#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly

zfs snapshot -r $TEST_ROOT@t0

system-replicate $TEST_ROOT $TEST_REPLICA

capture_status system-status replication
assert_command_ok replication should be up to date
echo "$OUTPUT" | assert_grep replication
echo "$OUTPUT" | assert_grep OK
