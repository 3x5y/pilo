#!/bin/sh
set -e

file=new-file.txt
mkfile data $file
capture_file $file
pilo ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection

pilo static-promote

# static manifest valid
assert_manifest_valid collection /$COLLECTION
# use system command which ignores empty manifests
pilo manifest-verify >/dev/null || fail pile manifest invalid
