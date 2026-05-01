#!/bin/sh
set -eu

zfs destroy -r $INTAKE

mkfile data file.txt

capture_status system-capture $TMP/file.txt

assert_command_fail "capture should fail without intake dataset"
echo "$OUTPUT" | assert_grep "missing required dataset"
