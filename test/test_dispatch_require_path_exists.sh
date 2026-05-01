#!/bin/sh
set -e

export SYSTEM_PATH=/does/not/exist

capture_status pilo status

assert_command_fail
echo "$OUTPUT" | assert_grep "path does not exist"
