#!/bin/sh
set -e

# no snapshot created

capture_status pilo recover

assert_command_fail
echo "$OUTPUT" | assert_grep "no snapshots"
