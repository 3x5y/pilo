#!/bin/sh
set -e

unset PILO_REPLICA_ROOT
unset PILO_SECONDARY_ROOTS
export PILO_REPLICA_ROOT PILO_SECONDARY_ROOTS

capture_status pilo recover

assert_command_fail
echo "$OUTPUT" | assert_grep "no secondary configured"
