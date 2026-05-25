#!/bin/sh
set -e

file=stuff.txt
dir=foo/bar
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$dir/$file" \
    | pilo rewrite

pilo content-promote

assert_file_exists /$STATIC/collection/$dir/$file
assert_not_exists /$PILE/out/collection/$dir/$file
