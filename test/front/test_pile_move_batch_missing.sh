#!/bin/sh
set -e

mkfile data a.txt
capture_file a.txt
pilo content-ingest

# NB tabs!!
capture_status pilo content-reorg "
mv	in/a.txt	sort/a.txt
mv	in/missing.txt	sort/missing.txt
"

assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR: file does not exist"

# nothing should have moved
assert_file_exists /$PILE/in/a.txt
assert_not_exists /$PILE/sort/a.txt
