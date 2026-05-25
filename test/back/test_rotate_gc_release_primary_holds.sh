#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot t1
pilo storage-replicate

pilo storage-snapshot t2
pilo storage-replicate

OUT=$(PILO_ROTATE_GC_KEEP=1 pilo storage-rotate-gc --preview 2>&1)
echo "$OUT" | assert_grep "release.*@t0"
echo "$OUT" | assert_grep "release.*@t1"
echo "$OUT" | assert_not_grep "release.*@t2"

PILO_ROTATE_GC_KEEP=1 pilo storage-rotate-gc

zfs holds -H $TEST_ROOT@t2 | assert_grep "pilo:tank"
zfs holds -H $TEST_ROOT@t1 | assert_not_grep "pilo:tank"
zfs list -t snapshot -Ho name $TEST_ROOT | assert_grep "@t1"
