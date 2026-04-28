#!/bin/sh
set -e

file=file.txt
dst=collection
mkfile data $file
capture_file $file
system-ingest-pile
# simulate interrupted promotion with copy
with_writable $STATIC/$dst \
    cp /$PILE/in/$file /$STATIC/$dst/$file
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/$dst/$file

system-static-promote

# invariant: only exists in static
assert_not_exists /$PILE/out/$dst/$file
assert_file_exists /$STATIC/$dst/$file
