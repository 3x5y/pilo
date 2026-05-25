#!/bin/sh
set -eu

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-replicate
pilo storage-replicate

zfs list -t snapshot | assert_grep $TEST_REPLICA@t0
count=$(zfs list -t snapshot | grep $TEST_REPLICA@ | wc -l)
[ $count -eq 1 ] || fail replication not idempotent
