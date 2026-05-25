#!/bin/sh
set -e

mkfile data file.txt
capture_file file.txt
pilo content-ingest

script=$(printf "mv\tin/$file")
capture_status pilo content-reorg "$script"

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid command"
