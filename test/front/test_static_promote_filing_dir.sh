#!/bin/sh
set -e

dir=a/b
file=file.txt
archive=filing/2025
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/$archive/$dir/$file" \
    | pilo rewrite
zfs create -p $STATIC/$archive
chown $PILO_USER:$PILO_USER /$STATIC/$archive

pilo static-promote

assert_file_exists /$STATIC/$archive/$dir/$file
