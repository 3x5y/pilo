#!/bin/sh
set -e

pilo snapshot baseline
pilo replica-seed

zfs destroy -r $TEST_ROOT

pilo recover >/dev/null

zfs list -t snapshot | assert_grep "$TEST_ROOT@baseline"
