#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot-reg
pilo storage-replicate

pilo storage-snapshot t1
pilo storage-replicate

# ensure incremental basis was the rpo snapshot (indirectly)
zfs list -t snap -Ho name $TEST_REPLICA | assert_grep "reg$"
