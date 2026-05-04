#!/bin/sh
set -eu

# Break the structure
zfs destroy "$PILO_ROOT/active/admin"

capture_status pilo doctor

assert_command_fail "doctor should fail on missing dataset"
echo "$OUTPUT" | assert_grep "missing required dataset"
