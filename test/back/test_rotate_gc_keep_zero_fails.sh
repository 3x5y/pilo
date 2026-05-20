#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

capture_status env PILO_ROTATE_GC_KEEP=0 pilo rotate-gc
assert_command_fail
echo "$OUTPUT" | assert_grep "keep must be >= 1"
