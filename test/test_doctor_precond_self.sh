#!/bin/sh
set -eu

# Break structure
zfs destroy "$PILO_ROOT/active/admin"

capture_status pilo doctor

assert_command_fail
echo "$OUTPUT" | assert_grep "missing required dataset"
