#!/bin/sh
set -e

file=nice.txt
mkfile data $file
capture_file $file
system-ingest-pile

with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection
system-static-promote

cat /$PILE/.manifest
assert_not_grep "./in/$file$" < /$PILE/.manifest
