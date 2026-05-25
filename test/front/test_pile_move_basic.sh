#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo content-ingest

printf "mv\tin/$file\tsort/$file" \
    | pilo content-reorg

assert_not_exists /$PILE/in/$file
assert_file_exists /$PILE/sort/$file
assert_manifest_valid pile /$PILE
