#!/bin/sh
set -e

system-snapshot-anchor

zfs list -t snapshot | assert_grep "$ACTIVE@a-"
zfs list -t snapshot | assert_grep "$STATIC@a-"
