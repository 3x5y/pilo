#!/bin/sh
set -e

file=some-file.txt
archive=filing/2025
mkfile data $file
capture_file $file
pilo ingest-pile
printf "mv\tin/$file\tout/$archive/$file" \
    | pilo rewrite
zfs create -p $STATIC/$archive

pilo static-promote

assert_file_exists /$STATIC/$archive/$file
assert_not_exists /$PILE/out/$archive/$file
