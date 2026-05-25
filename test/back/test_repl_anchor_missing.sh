#!/bin/sh
set -e

pilo storage-snapshot-reg
pilo storage-replica-seed

# destroy source snapshot
clear_holds
snap=$(zfs list -t snap -s creation -Ho name $TEST_ROOT \
        | grep "reg$" | tail -n1)
zfs destroy "$snap"

pilo storage-snapshot t1

capture_status pilo storage-replicate

assert_command_fail expected missing snapshot failure
echo "$OUTPUT" | assert_grep "ERROR: divergence"
