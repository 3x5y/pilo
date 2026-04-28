#!/bin/sh
set -e

mkfile a a.txt
mkfile b b.txt

capture_file a.txt
capture_file b.txt
system-ingest-pile

capture_status system-rewrite "
mv	in/a.txt	sort/x.txt
mv	in/b.txt	sort/x.txt
"

assert_command_fail
echo "$OUTPUT" | assert_grep 'ERROR: destination conflict'

# nothing moved
assert_file_exists /$PILE/in/a.txt
assert_file_exists /$PILE/in/b.txt
