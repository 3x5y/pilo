#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
system-ingest-pile

assert_file_exists /$PILE/in/$file
assert_manifest_valid /$PILE
assert_manifest_entry /$PILE " \./in/$file$"
