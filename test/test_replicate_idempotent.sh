#!/bin/sh
set -eu

system-snapshot t0
system-replicate

system-replicate

zfs list -t snapshot | assert_grep $TEST_REPLICA@t0
count=$(zfs list -t snapshot | grep $TEST_REPLICA@ | wc -l)
[ $count -eq 1 ] || fail replication not idempotent
