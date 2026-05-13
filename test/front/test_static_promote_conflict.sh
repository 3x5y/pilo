#!/bin/sh
set -e

file=conflict.txt
mkfile good $file
capture_file $file
pilo ingest-pile
printf "mv\tin/$file\tout/collection/$file" \
    | pilo rewrite
pilo static-promote
# reintroduce conflicting version
mkfile bad $file
capture_file $file
pilo ingest-pile
printf "mv\tin/$file\tout/collection/$file" \
    | pilo rewrite

capture_status pilo static-promote

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$file
# original must remain
assert_grep good < /$STATIC/collection/$file
