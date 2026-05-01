#!/bin/sh
set -eu

pilo snapshot t0
pilo replicate

pilo replicate

zfs list -t snapshot | assert_grep $TEST_REPLICA@t0
count=$(zfs list -t snapshot | grep $TEST_REPLICA@ | wc -l)
[ $count -eq 1 ] || fail replication not idempotent
