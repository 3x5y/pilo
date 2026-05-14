#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt

pilo ingest-pile

script=$(printf "rm\tin/a.txt")

capture_status pilo rewrite "$script"

assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR: rewrite contains removals"
