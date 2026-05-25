#!/bin/sh
set -e

echo v1 > $ADMIN_PATH/file.txt

pilo storage-snapshot t0
pilo storage-replica-seed

clear_holds
zfs destroy -r $TEST_ROOT
zfs create $TEST_ROOT

capture_status pilo storage-recover

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset exists"
