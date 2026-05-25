#!/bin/sh
set -e

file=ok.txt
mkfile ok $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$file" \
    | pilo rewrite

pilo static-promote

assert_not_exists /$PILE/out/collection/$file "file still in pile"
assert_file_exists /$STATIC/collection/$file "file not moved to filing"
