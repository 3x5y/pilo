#!/bin/sh
set -eu

# Break system
zfs destroy "$PILO_ROOT/active/admin"

mkfile "data" "file1"

capture_status pilo capture "$TMP/file1"

assert_command_fail
echo "$OUTPUT" | assert_grep "missing required dataset"
