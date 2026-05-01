#!/bin/sh
set -eu

# remove one required dataset
zfs destroy -r $TEST_ROOT/active/admin

capture_status system-init

assert_command_fail "init should fail on missing dataset"
echo "$OUTPUT" | assert_grep "missing required dataset"
