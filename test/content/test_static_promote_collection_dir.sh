#!/bin/sh
set -e

file=stuff.txt
dir=foo/bar

mkdir -p /$PILE/out/collection/$dir
echo data > /$PILE/out/collection/$dir/$file
create_pile_manifest

pilo content-promote

assert_file_exists /$STATIC/collection/$dir/$file
assert_not_exists /$PILE/out/collection/$dir/$file
