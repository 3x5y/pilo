#!/bin/sh
set -e

file=good-file.txt
mkfile good $file
capture_file $file
pilo ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$file

pilo static-promote

assert_manifest_entry collection " \./$file$"
assert_manifest_valid collection /$COLLECTION
