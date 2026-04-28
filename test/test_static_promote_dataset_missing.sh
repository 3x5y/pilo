#!/bin/sh
set -e

file=bad.txt
archive=filing/2099
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/$archive
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/$archive/$file

# dataset does NOT exist
capture_status system-static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "dataset does not exist"
