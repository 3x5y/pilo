#!/bin/sh
set -e

system-snapshot-anchor
system-replicate

zfs list -t snapshot | assert_grep "$TEST_REPLICA@a-"
