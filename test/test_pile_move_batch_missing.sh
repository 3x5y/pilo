#!/bin/sh
set -e

mkfile data a.txt
capture_file a.txt
system-ingest-pile

capture_status system-rewrite "
mv	in/a.txt	sort/a.txt
mv	in/missing.txt	sort/missing.txt
"

assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR: source missing"

# nothing should have moved
assert_file_exists /$PILE/in/a.txt
assert_not_exists /$PILE/sort/a.txt
