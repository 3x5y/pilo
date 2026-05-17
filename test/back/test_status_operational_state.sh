#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed
pilo replicate

capture_status pilo status

assert_command_ok
echo "$OUTPUT" | assert_grep "lifecycle: NORMAL"
