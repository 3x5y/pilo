#!/bin/sh
set -e

unset SYSTEM_PATH

capture_status pilo status

assert_command_fail
echo "$OUTPUT" | assert_grep "SYSTEM_PATH"
