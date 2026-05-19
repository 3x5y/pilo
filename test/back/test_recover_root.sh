#!/bin/sh
set -e

pilo snapshot baseline
pilo replica-seed

zfs destroy -r $TEST_ROOT

capture_status pilo recover
assert_command_ok

zfs list -t snapshot | assert_grep "$TEST_ROOT@baseline"
