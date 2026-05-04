#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo ingest-pile

assert_manifest_entry pile " \./in/$file$"
assert_manifest_valid pile /$PILE
