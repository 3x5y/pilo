#!/bin/sh
set -e

snap=baseline
pilo snapshot $snap
pilo replicate
zfs destroy -r $TEST_ROOT

# recover whole root, not per-dataset
pilo restore $TEST_REPLICA $TEST_ROOT $snap --recursive

zfs list -t snapshot | assert_grep "$TEST_ROOT@$snap"
