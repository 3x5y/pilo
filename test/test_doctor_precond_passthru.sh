#!/bin/sh
set -eu

zfs destroy "$PILO_ROOT/active/admin"

mkfile "data" "file1"

capture_status pilo capture "$TMP/file1"

assert_command_fail
echo "$OUTPUT" | assert_grep "$PILO_ROOT/active/admin"
