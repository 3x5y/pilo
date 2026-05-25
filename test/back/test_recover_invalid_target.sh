#!/bin/sh
set -e

pilo storage-snapshot baseline
pilo storage-replica-seed

clear_holds
zfs destroy -r $TEST_ROOT

path=/random/path
capture_status pilo storage-recover /random/path

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset outside root"
