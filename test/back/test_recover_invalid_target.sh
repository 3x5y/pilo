#!/bin/sh
set -e

path=/random/path
capture_status pilo recover /random/path

assert_command_fail
echo "$OUTPUT" | assert_grep "$path outside "
