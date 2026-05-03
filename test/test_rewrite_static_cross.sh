#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

script=$(printf "mv\tin/file.txt\tcollection/file.txt\n")
capture_status pilo rewrite "$script"

assert_command_fail
echo "$OUTPUT" | assert_grep "cross-domain"
