#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo ingest-pile

# NB tabs!!
printf "mv\tin/$file\tsort/2025/a/$file" \
    | pilo rewrite

assert_file_exists /$PILE/sort/2025/a/$file
assert_not_exists /$PILE/in/$file
assert_manifest_valid pile /$PILE
