#!/bin/sh
set -e

pilo snapshot-rpo
pilo snapshot-rpo
pilo replica-seed

zfs list -t snap -Ho name $TEST_REPLICA | assert_grep "incr$"
