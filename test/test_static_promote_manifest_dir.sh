#!/bin/sh
set -e

file=file.txt
dir=a/b
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/collection/$dir
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$dir/$file

system-static-promote

assert_manifest_entry /$STATIC " \./collection/$dir/$file$"
