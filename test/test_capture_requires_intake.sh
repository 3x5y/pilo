#!/bin/sh
set -e

zfs destroy -r $TEST_ROOT/active/pile-intake

mkfile data file.txt

capture_status system-capture $TMP/file.txt

assert_command_fail "capture should fail without intake dataset"
echo "$OUTPUT" | assert_grep "missing required dataset"
