#!/bin/sh
set -e

file=collected.txt
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$file" \
    | pilo rewrite

pilo content-promote

assert_file_exists /$STATIC/collection/$file
assert_not_exists /$PILE/out/collection/$file
