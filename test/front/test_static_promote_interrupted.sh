#!/bin/sh
set -e

file=file.txt
dst=collection
mkfile data $file
capture_file $file
pilo content-ingest
# simulate interrupted promotion with copy
with_writable $STATIC/$dst \
    cp /$PILE/in/$file /$STATIC/$dst/$file
printf "mv\tin/$file\tout/$dst/$file" \
    | pilo content-reorg

pilo content-promote

# invariant: only exists in static
assert_not_exists /$PILE/out/$dst/$file
assert_file_exists /$STATIC/$dst/$file
