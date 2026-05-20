#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

pilo snapshot t1
pilo replicate

pilo snapshot t2
pilo replicate

OUT=$(PILO_ROTATE_GC_KEEP=1 pilo rotate-gc --preview 2>&1)
echo "$OUT" | assert_grep "release.*@t0"
echo "$OUT" | assert_grep "release.*@t1"
echo "$OUT" | assert_not_grep "release.*@t2"

PILO_ROTATE_GC_KEEP=1 pilo rotate-gc

zfs holds -H $TEST_ROOT@t2 | assert_grep "pilo:tank"
zfs holds -H $TEST_ROOT@t1 | assert_not_grep "pilo:tank"
zfs list -t snapshot -Ho name $TEST_ROOT | assert_grep "@t1"
