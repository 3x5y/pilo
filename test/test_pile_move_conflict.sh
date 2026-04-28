#!/bin/sh
set -e

file=file.txt
mkfile good $file
capture_file $file
system-ingest-pile

# NB tabs!!
system-rewrite "mv	in/$file	sort/$file"

# recreate conflicting source
mkfile bad $file
capture_file $file
system-ingest-pile

# NB tabs!!
capture_status system-rewrite "mv	in/$file	sort/$file"

assert_command_fail
echo "$OUTPUT" | assert_grep conflict

# original must remain
assert_grep good < /$PILE/sort/$file
