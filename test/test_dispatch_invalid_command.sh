#!/bin/sh
set -e

capture_status pilo does-not-exist

assert_command_fail
echo "$OUTPUT" | assert_grep "unknown command"
