#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

capture_status env PILO_ROTATE_GC_KEEP=0 pilo storage-rotate-gc
assert_command_fail
echo "$OUTPUT" | assert_grep "keep must be >= 1"
