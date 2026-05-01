#!/bin/sh
set -eu

capture_status pilo

assert_command_fail
echo "$OUTPUT" | assert_grep "missing command"
