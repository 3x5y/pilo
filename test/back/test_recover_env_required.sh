#!/bin/sh
set -e

unset PILO_REPLICA_ROOT

capture_status pilo recover

assert_command_fail
echo "$OUTPUT" | assert_grep "PILO_REPLICA_ROOT"
