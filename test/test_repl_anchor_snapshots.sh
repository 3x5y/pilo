#!/bin/sh
set -e

system-anchor-create daily
system-anchor-create rotation
system-replicate

zfs list -t snap $TEST_REPLICA | assert_grep "@daily-"
zfs list -t snap $TEST_REPLICA | assert_grep "@rotation-"
