#!/bin/sh
set -e

mkfile data file1.txt
capture_file file1.txt
pilo ingest-pile
mkfile data file2.txt
capture_file file2.txt
pilo ingest-pile

printf "rm\tin/file1.txt" \
    | pilo rewrite --delete

assert_not_exists /$PILE/in/file1.txt
assert_file_exists /$PILE/in/file2.txt
assert_manifest_valid pile /$PILE

