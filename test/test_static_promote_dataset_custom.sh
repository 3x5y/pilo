#!/bin/sh
set -e

file=old-file.txt
archive=filing/1990-2000
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/$archive
with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/$archive/$file
zfs create -p -o readonly=on $STATIC/$archive

system-static-promote

assert_file_exists /$STATIC/$archive/$file
