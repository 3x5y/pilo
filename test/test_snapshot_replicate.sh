#!/bin/sh
set -e

snap=baseline
pilo-snapshot $snap
pilo-replicate

zfs list -t snapshot | assert_grep $TEST_REPLICA@$snap
zfs list -t snapshot | assert_grep $TEST_REPLICA/active@$snap
