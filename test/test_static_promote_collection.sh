#!/bin/sh
set -e

file=collected.txt
mkfile data $file
capture_file $file
pilo-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$file

pilo-static-promote

assert_file_exists /$STATIC/collection/$file
assert_not_exists /$PILE/out/collection/$file
