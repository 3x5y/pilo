#!/bin/sh
set -e

zfs destroy -r $TEST_ROOT

pilo storage-provision-primary

capture_status pilo storage-provision-primary

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset exists"
