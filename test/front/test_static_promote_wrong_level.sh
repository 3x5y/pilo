#!/bin/sh
set -e

file=bad.txt
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/filing/$file" \
    | pilo content-reorg

capture_status pilo content-promote

assert_command_fail accepted invalid structure
echo "$OUTPUT" | assert_grep "invalid filing structure"
