#!/bin/sh
set -e

system-snapshot baseline
system-replicate
zfs destroy -r $TEST_ROOT

# recover whole root, not per-dataset
system-recover-tree $TEST_REPLICA $TEST_ROOT baseline

zfs list -t snapshot | assert_grep "$TEST_ROOT@baseline"
