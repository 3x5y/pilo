#!/bin/sh
set -e

file=bad.txt
archive=filing/2099
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/$archive/$file" \
    | pilo rewrite

# dataset does NOT exist
capture_status pilo static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "missing required dataset"
