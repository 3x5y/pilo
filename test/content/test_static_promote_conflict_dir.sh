#!/bin/sh
set -e

file=dir-conflict.txt
dir=x/y
mkfile good-data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$dir/$file" \
    | pilo content-reorg
pilo content-promote
# reintroduce conflicting version
mkfile bad-data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$dir/$file" \
    | pilo content-reorg

capture_status pilo content-promote

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$file
# original must remain
assert_grep good-data < /$STATIC/collection/$dir/$file

