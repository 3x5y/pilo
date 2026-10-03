#!/bin/sh
set -e

pilo storage-snapshot baseline

zfs list -t snapshot | assert_grep "$TEST_ROOT@baseline"
zfs list -t snapshot | assert_grep "$TEST_ROOT/admin@baseline"
zfs list -t snapshot | assert_grep "$TEST_ROOT/static@baseline"
