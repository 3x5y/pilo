#!/bin/sh
set -e

SRC=$TEST_ROOT
DST=$TEST_REPLICA

system-snapshot baseline
system-replicate "$SRC" "$DST"

zfs list -t snapshot | assert_grep "$DST@baseline"
zfs list -t snapshot | assert_grep "$DST/active@baseline"
