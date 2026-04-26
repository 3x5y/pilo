#!/bin/sh
set -e

ROOT=$TEST_ROOT

system-snapshot baseline

zfs list -t snapshot | assert_grep "$ROOT@baseline"
zfs list -t snapshot | assert_grep "$ROOT/active@baseline"
zfs list -t snapshot | assert_grep "$ROOT/static@baseline"
