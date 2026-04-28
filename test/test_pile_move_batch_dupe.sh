#!/bin/sh
set -e

mkfile data a.txt
capture_file a.txt
system-ingest-pile

capture_status system-rewrite "
mv	in/a.txt	sort/a.txt
mv	in/a.txt	sort/b.txt
"

assert_command_fail
echo "$OUTPUT"
echo "$OUTPUT" | assert_grep 'ERROR: duplicate source'

# unchanged
assert_file_exists /$PILE/in/a.txt
