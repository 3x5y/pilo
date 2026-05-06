#!/bin/sh
set -e

capture_status pilo recover /random/path

assert_command_fail
echo "$OUTPUT" | assert_grep "outside source root"
