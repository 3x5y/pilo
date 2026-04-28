#!/bin/sh
set -e

capture_status system-rewrite "mv	in/a.txt	sort/a.txt	extra"

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid command"
