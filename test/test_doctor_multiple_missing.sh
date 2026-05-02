#!/bin/sh
set -e

zfs destroy "$PILO_ROOT/active/admin"
zfs destroy "$PILO_ROOT/active/pile-intake"

capture_status pilo doctor

assert_command_fail "doctor should fail"
echo "$OUTPUT" | assert_grep "$PILO_ROOT/active/admin"
echo "$OUTPUT" | assert_grep "$PILO_ROOT/active/pile-intake"
