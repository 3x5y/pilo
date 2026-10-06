#!/bin/sh
set -e

file=file.txt
dst=collection/a
mkdir -p /$PILE/out/$dst
echo data > /$PILE/out/$dst/$file
create_pile_manifest

pilo content-promote

# reintroduce identical
echo data > /$PILE/out/$dst/$file

pilo content-promote

assert_file_exists /$STATIC/$dst/$file
assert_not_exists /$PILE/out/$dst/$file
pilo manifest-verify >/dev/null
