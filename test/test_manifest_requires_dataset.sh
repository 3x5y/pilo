#!/bin/sh
set -eu

zfs destroy -r $PILE

capture_status system-manifest-update

assert_command_fail "manifest update should fail without pile"
echo "$OUTPUT" | assert_grep "missing required dataset"
