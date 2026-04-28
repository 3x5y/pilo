#!/bin/sh
set -e

file=new-file.txt
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection

system-static-promote

# static manifest valid
assert_manifest_valid /$STATIC
# use system command which ignores empty manifests
system-manifest-verify || fail pile manifest invalid
