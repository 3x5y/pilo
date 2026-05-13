#!/bin/sh
set -e

file=bad.txt
mkfile data $file
capture_file $file
pilo ingest-pile
printf "mv\tin/$file\tout/filing/$file" \
    | pilo rewrite

capture_status pilo static-promote

assert_command_fail accepted invalid structure
echo "$OUTPUT" | assert_grep "invalid filing structure"
