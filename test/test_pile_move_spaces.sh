#!/bin/sh
set -e

file="file with space.txt"

mkfile data "$file"
capture_file "$file"
system-ingest-pile

# NB tabs!!
system-rewrite "mv	in/$file	sort/$file"

assert_file_exists /$PILE/sort/"$file"
assert_not_exists /$PILE/in/"$file"
