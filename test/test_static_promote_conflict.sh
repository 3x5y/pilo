#!/bin/sh
set -e

file=conflict.txt
mkfile good $file
capture_file $file
pilo-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection
pilo-static-promote
# reintroduce conflicting version
mkfile bad $file
capture_file $file
pilo-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection

capture_status pilo-static-promote

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$file
# original must remain
assert_grep good < /$STATIC/collection/$file
