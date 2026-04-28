#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
system-ingest-pile

# reorganise
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/sort/$file
system-manifest-update

assert_grep " \./sort/$file$" < /$PILE/.manifest
assert_not_grep " \./in/$file$" < /$PILE/.manifest
assert_manifest_valid /$PILE
