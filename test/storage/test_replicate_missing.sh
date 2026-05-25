#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed
# destroy base snapshot on source → break incremental chain
clear_holds
zfs destroy $TEST_ROOT@t0
pilo storage-snapshot t1

capture_status pilo storage-replicate

assert_command_fail
#echo "$OUTPUT" | assert_grep "ERROR: base snapshot missing"
echo "$OUTPUT" | assert_grep "ERROR: divergence"
