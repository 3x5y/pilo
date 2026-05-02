#!/bin/sh
set -eu

zfs set readonly=off "$PILE"

capture_status pilo doctor

assert_command_fail
echo "$OUTPUT" | assert_grep "not readonly"
