#!/bin/sh
set -e

unset PILO_SECONDARY_ROOTS
export PILO_SECONDARY_ROOTS

capture_status pilo storage-recover

assert_command_fail
echo "$OUTPUT" | assert_grep "no secondary configured"
