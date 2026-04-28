#!/bin/sh
set -e

FILE=file.txt

mkfile good $FILE
capture_file $FILE
system-ingest-pile

system-rewrite "mv in/$FILE sort/$FILE"

# recreate conflicting source
mkfile bad $FILE
capture_file $FILE
system-ingest-pile

capture_status system-rewrite "mv in/$FILE sort/$FILE"

assert_command_fail
echo "$OUTPUT" | assert_grep conflict

# original must remain
assert_grep good < /$PILE/sort/$FILE
