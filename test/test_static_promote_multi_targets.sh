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
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/$archive_a
with_writable $PILE \
    mv /$PILE/in/$a /$PILE/out/$archive_a/$a
with_writable $PILE \
    mkdir -p /$PILE/out/$archive_b
with_writable $PILE \
    mv /$PILE/in/$b /$PILE/out/$archive_b/$b
zfs create -p -o readonly=on $STATIC/$archive_a

system-static-promote

assert_file_exists /$STATIC/$archive_a/$a
assert_file_exists /$STATIC/$archive_b/$b
