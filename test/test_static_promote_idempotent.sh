#!/bin/sh
set -e

file=file.txt
dst=collection/a
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/$dst
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/$dst
system-static-promote
# reintroduce identical
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/$dst

system-static-promote

assert_file_exists /$STATIC/$dst/$file
assert_not_exists /$PILE/out/$dst/$file
