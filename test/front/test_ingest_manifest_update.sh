#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
pilo ingest-pile

assert_file_exists /$PILE/in/$file
assert_manifest_valid pile /$PILE
assert_manifest_entry pile " \./in/$file$"
