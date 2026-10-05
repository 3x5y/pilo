#!/bin/sh
set -e

file=file.txt
dst=collection
echo data > /$PILE/in/$file
# simulate interrupted promotion with copy
with_writable $STATIC/$dst \
    cp /$PILE/in/$file /$STATIC/$dst/$file
mv /$PILE/in/$file /$PILE/out/$dst/$file

pilo content-promote

# invariant: only exists in static
assert_not_exists /$PILE/out/$dst/$file
assert_file_exists /$STATIC/$dst/$file
