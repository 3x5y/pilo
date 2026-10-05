#!/bin/sh
set -e

file=dir-conflict.txt
dir=x/y

mkdir -p /$PILE/out/collection/$dir
echo good-data > /$PILE/out/collection/$dir/$file
create_pile_manifest
pilo content-promote

echo bad > /$PILE/out/collection/$dir/$file

capture_status pilo content-promote

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$file
# original must remain
assert_grep good-data < /$STATIC/collection/$dir/$file

