#!/bin/sh
set -e

file=some-file.txt
archive=filing/2025
mkdir -p /$PILE/out/$archive
echo data > /$PILE/out/$archive/$file
create_pile_manifest
zfs create -p -o readonly=on $STATIC/$archive

pilo content-promote

assert_file_exists /$STATIC/$archive/$file
assert_not_exists /$PILE/out/$archive/$file
