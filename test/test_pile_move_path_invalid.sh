#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
system-ingest-pile

# NB tabs!!
capture_status system-rewrite "mv	in/$file	../evil.txt"

assert_command_fail
echo "$OUTPUT" | assert_grep invalid
