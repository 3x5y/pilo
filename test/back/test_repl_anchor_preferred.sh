#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

pilo snapshot-rpo
pilo replicate

pilo snapshot t1
pilo replicate

# ensure incremental basis was the rpo snapshot (indirectly)
zfs list -t snap -Ho name $TEST_REPLICA | assert_grep "incr$"
