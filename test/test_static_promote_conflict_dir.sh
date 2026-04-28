#!/bin/sh
set -e

file=dir-conflict.txt
dir=x/y
with_writable $PILE \
    mkdir -p /$PILE/out/collection/$dir
mkfile good-data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$dir
system-static-promote
# reintroduce conflicting version
mkfile bad-data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection/$dir

capture_status system-static-promote

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$file
# original must remain
assert_grep good-data < /$STATIC/collection/$dir/$file

