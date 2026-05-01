#!/bin/sh
set -e

unset SYSTEM_ROOT

capture_status system system-status

assert_command_fail
echo "$OUTPUT" | assert_grep "SYSTEM_ROOT"
