#!/bin/sh
set -e

unset PILO_CONFIG
unset PILO_ROOT
unset PILO_PATH

capture_status pilo status pile

assert_command_fail
echo "$OUTPUT" | assert_grep "PILO_ROOT not set"
