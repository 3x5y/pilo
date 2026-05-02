#!/bin/sh
set -e

export PILO_ROOT=nonexistent/dataset

capture_status pilo status

assert_command_fail
echo "$OUTPUT" | assert_grep "missing required dataset"
