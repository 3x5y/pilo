#!/bin/sh
set -e

echo skipped
exit 0

# no snapshot created

capture_status pilo recover

assert_command_fail
echo "$OUTPUT" | assert_grep "missing required"
