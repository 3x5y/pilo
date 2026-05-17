#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

# break it
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status pilo replicate-safe

assert_command_fail expected divergence
echo "$OUTPUT" | assert_grep divergence
