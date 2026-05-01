#!/bin/sh
set -e

export SYSTEM_ROOT=nonexistent/dataset

capture_status pilo status

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset does not exist"
