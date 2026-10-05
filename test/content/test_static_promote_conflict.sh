#!/bin/sh
set -e

file=conflict.txt
echo good > /$PILE/out/collection/$file
create_pile_manifest
pilo content-promote

# reintroduce conflicting version
echo bad > /$PILE/out/collection/$file

capture_status pilo content-promote

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$file
# original must remain
assert_grep good < /$STATIC/collection/$file
