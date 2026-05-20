#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

clear_holds

pilo rotate-gc

zfs list -t snapshot -Ho name $TEST_REPLICA | assert_not_grep "@t0"
zfs list -t snapshot -Ho name $TEST_ROOT | assert_not_grep "@t0"
