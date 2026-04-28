#!/bin/sh
set -e

system-snapshot t0
system-replicate
# destroy base snapshot on source → break incremental chain
zfs destroy $TEST_ROOT@t0
system-snapshot t1

capture_status system-replicate

assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR: base snapshot missing"
