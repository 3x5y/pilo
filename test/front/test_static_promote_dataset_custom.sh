#!/bin/sh
set -e

file=old-file.txt
archive=filing/1990-2000
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/$archive/$file" \
    | pilo content-reorg
zfs create -p -o readonly=on $STATIC/$archive

pilo content-promote

assert_file_exists /$STATIC/$archive/$file
