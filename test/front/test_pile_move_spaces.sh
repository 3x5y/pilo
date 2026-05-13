#!/bin/sh
set -e

file="file with space.txt"

mkfile data "$file"
capture_file "$file"
pilo ingest-pile

printf "mv\tin/$file\tsort/$file" \
    | pilo rewrite

assert_file_exists /$PILE/sort/"$file"
assert_not_exists /$PILE/in/"$file"
