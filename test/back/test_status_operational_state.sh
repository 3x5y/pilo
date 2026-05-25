#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed
pilo storage-replicate

capture_status pilo status

assert_command_ok
echo "$OUTPUT" | assert_grep "lifecycle.state: NORMAL"
