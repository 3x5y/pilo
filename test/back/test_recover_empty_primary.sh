#!/bin/sh
set -e

echo v1 > $ADMIN_PATH/file.txt

pilo snapshot t0
pilo replica-seed

zfs destroy -r $TEST_ROOT
zfs create $TEST_ROOT

capture_status pilo recover

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset exists"
