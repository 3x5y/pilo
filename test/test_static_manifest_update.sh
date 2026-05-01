#!/bin/sh
set -e

file=manifest-item.txt
mkfile important $file
capture_file $file
pilo ingest-pile
pilo manifest-update
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$file

pilo static-promote

#assert_grep " \./collection/$file$" < /$STATIC/.manifest
assert_manifest_entry /$STATIC " \./collection/$file$"
assert_manifest_valid /$STATIC
