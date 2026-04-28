#!/bin/sh
set -e

mkfile a a.txt
mkfile b b.txt

capture_file a.txt
capture_file b.txt
system-ingest-pile

# NB tabs!!
system-rewrite "
mv	in/a.txt	sort/a.txt
mv	in/b.txt	sort/b.txt
"

assert_file_exists /$PILE/sort/a.txt
assert_file_exists /$PILE/sort/b.txt

assert_manifest_valid /$PILE
