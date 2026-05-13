#!/bin/sh
set -e

script=$(printf "mv\tin/a.txt\tsort/a.txt\textra stuff")
capture_status pilo rewrite "$script"

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid command"
