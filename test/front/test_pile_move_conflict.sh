#!/bin/sh
set -e

file=file.txt
mkfile good $file
capture_file $file
pilo ingest-pile

script=$(printf "mv\tin/$file\tsort/$file")
pilo rewrite "$script"

# recreate conflicting source
mkfile bad $file
capture_file $file
pilo ingest-pile

capture_status pilo rewrite "$script"

assert_command_fail
echo "$OUTPUT" | assert_grep conflict

# original must remain
assert_grep good < /$PILE/sort/$file
