#!/bin/sh
set -e

dir=a/b
file=file.txt
archive=filing/2025
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/$archive/$dir
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/$archive/$dir
zfs create -p $STATIC/$archive

system-static-promote

assert_file_exists /$STATIC/$archive/$dir/$file
