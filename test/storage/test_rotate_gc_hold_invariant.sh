#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-snapshot t1
pilo storage-replica-seed

pilo storage-snapshot t2
zfs hold external-hold $TEST_ROOT@t2

pilo storage-rotate-gc

# oldest unheld snapshot destroyed
zfs list -t snapshot -Ho name $TEST_ROOT | assert_not_grep "@t0"
# pilo-held snapshot survives
zfs list -t snapshot -Ho name $TEST_ROOT | assert_grep "@t1"
# non-pilo hold survives and protects snapshot
zfs list -t snapshot -Ho name $TEST_ROOT | assert_grep "@t2"
zfs holds -H $TEST_ROOT@t2 | assert_grep "external-hold"
