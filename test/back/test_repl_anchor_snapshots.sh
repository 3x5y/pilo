#!/bin/sh
set -e

pilo storage-snapshot-reg
pilo storage-snapshot-reg
pilo storage-replica-seed

zfs list -t snap -Ho name $TEST_REPLICA | assert_grep "reg$"
