#!/bin/sh
set -eu

zfs destroy -r $PILE

capture_status pilo manifest-update

assert_command_fail
echo "$OUTPUT" | assert_grep "does not exist"
