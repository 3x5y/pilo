#!/bin/sh
set -eu

zfs destroy -r $TEST_ROOT/active/admin

capture_status system-status datasets

assert_command_fail "status should fail on incomplete system"
echo "$OUTPUT" | assert_grep "incomplete"
