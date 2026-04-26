#!/bin/sh
set -e

system-snapshot baseline
system-replicate

zfs list -t snapshot | assert_grep $TEST_REPLICA@baseline
zfs list -t snapshot | assert_grep $TEST_REPLICA/active@baseline
