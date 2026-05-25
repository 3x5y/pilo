#!/bin/sh
set -e

# no snapshot created

capture_status pilo storage-recover

assert_command_fail
echo "$OUTPUT" | assert_grep "secondary dataset missing"
