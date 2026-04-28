#!/bin/sh
set -e

file=good-file.txt
mkfile good $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$file

system-static-promote

assert_manifest_entry /$STATIC " \./collection/$file$"
assert_manifest_valid /$STATIC
