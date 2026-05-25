#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$file" \
    | pilo rewrite
pilo content-promote

# second promotion attempt (no re-ingest)
capture_status pilo content-promote

assert_command_fail expected missing source failure
echo "$OUTPUT" | assert_grep "/out/ directory empty"
