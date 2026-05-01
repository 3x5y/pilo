#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo-ingest-pile

# NB tabs!!
capture_status pilo-rewrite "mv	in/$file	../evil.txt"

assert_command_fail
echo "$OUTPUT" | assert_grep invalid
