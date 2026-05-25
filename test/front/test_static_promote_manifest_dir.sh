#!/bin/sh
set -e

file=file.txt
dir=a/b
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$dir/$file" \
    | pilo content-reorg

pilo content-promote

assert_manifest_entry collection " \./$dir/$file$"
