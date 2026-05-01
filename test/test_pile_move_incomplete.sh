#!/bin/sh
set -e

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

# NB tabs!!
capture_status pilo rewrite "mv	in/file.txt"

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid command"
