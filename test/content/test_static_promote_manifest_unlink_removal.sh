#!/bin/sh
set -eu

file=identical.txt

# identical destination already exists, so promotion is unlink-only
with_writable $COLLECTION \
    sh -c "echo data > '/$STATIC/collection/$file'"

echo data > /$PILE/out/collection/$file

# a pile file outside /out is not promoted and keeps the manifest non-empty
echo keep > /$PILE/in/keep.txt

create_pile_manifest

pilo content-promote

# source removed from pile, identical destination kept
assert_not_exists /$PILE/out/collection/$file
assert_file_exists /$STATIC/collection/$file
assert_grep "^data$" < /$STATIC/collection/$file

# pile manifest entry for the unlinked source is gone, unrelated entry stays
manifest=/$ADMIN/manifest/pile.manifest
assert_not_grep "\./out/collection/$file\$" < $manifest
assert_grep "\./in/keep\.txt\$" < $manifest

# promotion left a consistent pile manifest
assert_manifest_valid pile /$PILE
pilo manifest-verify >/dev/null || fail "pile manifest invalid after unlink-only promote"