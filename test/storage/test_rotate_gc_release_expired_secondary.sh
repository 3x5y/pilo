#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot t1
pilo storage-replicate

zfs release pilo:tank $TEST_ROOT@t0
zfs destroy $TEST_ROOT@t0

OUT=$(pilo storage-rotate-gc --preview 2>&1)
echo "$OUT" | assert_grep "release.*$TEST_REPLICA.*@t0"

pilo storage-rotate-gc

zfs holds -H $TEST_REPLICA@t0 | assert_not_grep "pilo:tank"
zfs list -t snapshot -Ho name $TEST_REPLICA | assert_grep "@t0"

# boundary invariant: current snapshot still held
zfs holds -H $TEST_REPLICA@t1 | assert_grep "pilo:tank"
