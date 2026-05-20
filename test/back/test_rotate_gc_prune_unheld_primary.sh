#!/bin/sh
set -e

pilo snapshot t0
pilo snapshot t1
pilo replica-seed

pilo rotate-gc

zfs list -t snapshot -Ho name $TEST_ROOT | assert_not_grep "@t0"
zfs list -t snapshot -Ho name $TEST_ROOT | assert_grep "@t1"
