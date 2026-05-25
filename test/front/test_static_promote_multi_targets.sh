#!/bin/sh
set -e

a=a.txt
b=b.txt
archive_a=filing/2024
archive_b=filing/2025
mkfile a $a
mkfile b $b
capture_file $a
capture_file $b
pilo content-ingest
printf "mv\tin/$a\tout/$archive_a/$a" \
    | pilo rewrite
printf "mv\tin/$b\tout/$archive_b/$b" \
    | pilo rewrite
zfs create -p -o readonly=on $STATIC/$archive_a
zfs create -p -o readonly=on $STATIC/$archive_b

pilo static-promote

assert_file_exists /$STATIC/$archive_a/$a
assert_file_exists /$STATIC/$archive_b/$b
