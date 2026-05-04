#!/bin/sh
set -eu

# remove one required dataset
zfs destroy -r $ADMIN

capture_status pilo init

assert_command_fail "init should fail on missing dataset"
echo "$OUTPUT" | assert_grep "missing required dataset"
