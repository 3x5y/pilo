#!/bin/sh
set -e

pilo snapshot-rpo
pilo replica-seed

# destroy source snapshot
snap=$(zfs list -t snap -s creation -Ho name $TEST_ROOT \
        | grep @r- | tail -n1)
zfs destroy "$snap"

pilo snapshot t1

capture_status pilo replicate

assert_command_fail expected missing snapshot failure
echo "$OUTPUT" | assert_grep "ERROR: divergence"
