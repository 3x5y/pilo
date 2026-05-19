#!/bin/sh
set -e

zfs destroy -r $TEST_ROOT

pilo provision-primary

capture_status pilo provision-primary

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset exists"
