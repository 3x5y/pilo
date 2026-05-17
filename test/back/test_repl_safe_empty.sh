#!/bin/sh
set -e

pilo snapshot t0

capture_status pilo replicate-safe

assert_command_fail
echo "$OUTPUT" | assert_grep "^ERROR: replica is uninitialized"
