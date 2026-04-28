#!/bin/sh
set -e

snap=baseline
system-snapshot $snap
system-replicate

zfs list -t snapshot | assert_grep $TEST_REPLICA@$snap
zfs list -t snapshot | assert_grep $TEST_REPLICA/active@$snap
