#!/bin/sh
set -e

pilo snapshot baseline

zfs list -t snapshot | assert_grep "$TEST_ROOT@baseline"
zfs list -t snapshot | assert_grep "$TEST_ROOT/active@baseline"
zfs list -t snapshot | assert_grep "$TEST_ROOT/static@baseline"
