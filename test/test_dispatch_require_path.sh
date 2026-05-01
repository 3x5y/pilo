#!/bin/sh
set -e

unset PILO_PATH

capture_status pilo status

assert_command_fail
echo "$OUTPUT" | assert_grep "PILO_PATH"
