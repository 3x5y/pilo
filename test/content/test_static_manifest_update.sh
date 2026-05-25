#!/bin/sh
set -e

file=manifest-item.txt
mkfile important $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$file" \
    | pilo content-reorg

pilo content-promote

assert_manifest_entry collection " \./$file$"
assert_manifest_valid collection /$COLLECTION
