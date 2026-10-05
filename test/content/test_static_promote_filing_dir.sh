#!/bin/sh
set -e

file=file.txt
dir=a/b
archive=filing/2025
mkdir -p /$PILE/out/$archive/$dir
echo data > /$PILE/out/$archive/$dir/$file
create_pile_manifest
zfs create -p -o readonly=on $STATIC/$archive

pilo content-promote

assert_file_exists /$STATIC/$archive/$dir/$file
