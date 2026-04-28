#!/bin/sh
set -e

file=stuff.txt
dir=foo/bar
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/collection/$dir
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$dir

system-static-promote

assert_file_exists /$STATIC/collection/$dir/$file
assert_not_exists /$PILE/out/collection/$dir/$file
