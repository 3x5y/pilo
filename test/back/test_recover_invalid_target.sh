#!/bin/sh
set -e

pilo snapshot baseline
pilo replica-seed

zfs destroy -r $TEST_ROOT

path=/random/path
capture_status pilo recover /random/path

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset outside root"
