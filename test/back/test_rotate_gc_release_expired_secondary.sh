#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

pilo snapshot t1
pilo replicate

zfs release pilo:tank $TEST_ROOT@t0
zfs destroy $TEST_ROOT@t0

OUT=$(pilo rotate-gc --preview 2>&1)
echo "$OUT" | assert_grep "release.*$TEST_REPLICA.*@t0"

pilo rotate-gc

zfs holds -H $TEST_REPLICA@t0 | assert_not_grep "pilo:tank"
zfs list -t snapshot -Ho name $TEST_REPLICA | assert_grep "@t0"

# boundary invariant: current snapshot still held
zfs holds -H $TEST_REPLICA@t1 | assert_grep "pilo:tank"
