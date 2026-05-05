#!/bin/sh
set -e

pilo snapshot t0
pilo replicate

pilo anchor-create rotation
pilo replicate

pilo snapshot t1
pilo replicate

# ensure incremental basis was anchor (indirectly)
zfs list -t snap $TEST_REPLICA | assert_grep rotation-
