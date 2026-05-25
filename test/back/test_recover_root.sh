#!/bin/sh
set -e

pilo storage-snapshot baseline
pilo storage-replica-seed

clear_holds
zfs destroy -r $TEST_ROOT

capture_status pilo storage-recover
assert_command_ok

zfs list -t snapshot | assert_grep "$TEST_ROOT@baseline"
