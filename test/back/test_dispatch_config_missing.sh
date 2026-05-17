#!/bin/sh
set -e

unset PILO_CONFIG
unset PILO_PATH
unset PILO_PRIMARY_ROOT

capture_status pilo status pile

assert_command_fail
echo "$OUTPUT" | assert_grep "PILO_PRIMARY_ROOT not set"
