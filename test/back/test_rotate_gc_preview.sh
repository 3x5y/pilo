#!/bin/sh
set -e

pilo snapshot t0
pilo snapshot t1
pilo replica-seed

OUT=$(pilo rotate-gc --preview 2>&1)
echo "$OUT" | assert_grep "destroy.*@t0"
echo "$OUT" | assert_not_grep "destroy.*@t1"

zfs list -t snapshot -Ho name $TEST_ROOT | assert_grep "@t0"
