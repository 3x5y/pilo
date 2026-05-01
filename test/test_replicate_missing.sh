#!/bin/sh
set -e

pilo-snapshot t0
pilo-replicate
# destroy base snapshot on source → break incremental chain
zfs destroy $TEST_ROOT@t0
pilo-snapshot t1

capture_status pilo-replicate

assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR: base snapshot missing"
