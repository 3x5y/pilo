#!/bin/sh
set -e

file=ok.txt
mkfile ok $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection

system-static-promote

assert_not_exists /$PILE/out/collection/$file "file still in pile"
assert_file_exists /$STATIC/collection/$file "file not moved to filing"
