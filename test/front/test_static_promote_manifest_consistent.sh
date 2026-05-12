#!/bin/sh
set -e

file=new-file.txt
mkfile data $file
capture_file $file
pilo ingest-pile
pilo rewrite "$(printf "mv\tin/$file\tout/collection/$file")"

pilo static-promote

# static manifest valid
assert_manifest_valid collection /$COLLECTION
# use system command which ignores empty manifests
pilo manifest-verify >/dev/null || fail pile manifest invalid
