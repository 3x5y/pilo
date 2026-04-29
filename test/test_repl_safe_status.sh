#!/bin/sh
set -e

system-snapshot t0
system-replicate

# break it
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status system-replicate-safe

assert_command_fail expected divergence
echo "$OUTPUT" | assert_grep DIVERGED
