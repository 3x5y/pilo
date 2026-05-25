#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-snapshot t1
pilo storage-replica-seed

pilo storage-rotate-gc

zfs list -t snapshot -Ho name $TEST_ROOT | assert_not_grep "@t0"
zfs list -t snapshot -Ho name $TEST_ROOT | assert_grep "@t1"
