#!/bin/sh
set -e

mkfile data file.txt
capture_file file.txt
system-ingest-pile

capture_status system-rewrite "mv in/file.txt"

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid command"
