#!/bin/sh
set -e

pilo storage-snapshot t0

capture_status pilo storage-replicate-safe

assert_command_fail
echo "$OUTPUT" | assert_grep "^ERROR: secondary dataset missing"
