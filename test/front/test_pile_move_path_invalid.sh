#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo content-ingest

script=$(printf "mv\tin/$file\t../evil.txt")

capture_status pilo content-reorg "$script"

assert_command_fail
echo "$OUTPUT" | assert_grep traversal not allowed
