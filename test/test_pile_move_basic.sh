#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo-ingest-pile

# NB tabs!!
pilo-rewrite "mv	in/$file	sort/$file"

assert_not_exists /$PILE/in/$file
assert_file_exists /$PILE/sort/$file
assert_manifest_valid /$PILE
