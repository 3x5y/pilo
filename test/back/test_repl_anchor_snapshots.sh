#!/bin/sh
set -e

pilo snapshot-incr
pilo snapshot-incr
pilo replica-seed

zfs list -t snap -Ho name $TEST_REPLICA | assert_grep "incr$"
