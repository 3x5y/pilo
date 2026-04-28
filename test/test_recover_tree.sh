#!/bin/sh
set -e

snap=baseline
system-snapshot $snap
system-replicate
zfs destroy -r $TEST_ROOT

# recover whole root, not per-dataset
system-recover-tree $TEST_REPLICA $TEST_ROOT $snap

zfs list -t snapshot | assert_grep "$TEST_ROOT@$snap"
