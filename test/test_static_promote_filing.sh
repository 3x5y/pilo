#!/bin/sh
set -e

file=some-file.txt
archive=filing/2025
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/$archive
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/$archive/$file

system-static-promote

assert_file_exists /$STATIC/$archive/$file
assert_not_exists /$PILE/out/$archive/$file
