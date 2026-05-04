#!/bin/sh
set -e

unset PILO_ROOT

capture_status pilo status

assert_command_fail
echo "$OUTPUT" | assert_grep "PILO_ROOT"
