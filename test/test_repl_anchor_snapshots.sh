#!/bin/sh
set -e

pilo-anchor-create daily
pilo-anchor-create rotation
pilo-replicate

zfs list -t snap $TEST_REPLICA | assert_grep "@daily-"
zfs list -t snap $TEST_REPLICA | assert_grep "@rotation-"
