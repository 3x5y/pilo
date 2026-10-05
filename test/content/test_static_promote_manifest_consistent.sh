#!/bin/sh
set -e

file=new-file.txt
echo data > /$PILE/out/collection/$file
create_pile_manifest

pilo content-promote

# static manifest valid
assert_manifest_valid collection /$COLLECTION
# use system command which ignores empty manifests
pilo manifest-verify >/dev/null || fail pile manifest invalid
