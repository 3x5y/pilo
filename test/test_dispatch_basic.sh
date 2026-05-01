#!/bin/sh
set -eu

capture_status system

assert_command_fail
echo "$OUTPUT" | assert_grep "missing command"
