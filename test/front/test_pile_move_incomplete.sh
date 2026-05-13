#!/bin/sh
set -e

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

script=$(printf "mv\tin/$file")
capture_status pilo rewrite "$script"

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid command"
