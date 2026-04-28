#!/bin/sh
set -e

FILE=file.txt

mkfile data $FILE
capture_file $FILE
system-ingest-pile

capture_status system-rewrite "mv in/$FILE ../evil.txt"

assert_command_fail
echo "$OUTPUT" | assert_grep invalid
