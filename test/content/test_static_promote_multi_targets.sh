#!/bin/sh
set -e

a=a.txt
b=b.txt
archive_a=filing/2024
archive_b=filing/2025
mkdir -p /$PILE/out/$archive_a
mkdir -p /$PILE/out/$archive_b
echo a > /$PILE/out/$archive_a/$a
echo b > /$PILE/out/$archive_b/$b
create_pile_manifest

zfs create -p -o readonly=on $STATIC/$archive_a
zfs create -p -o readonly=on $STATIC/$archive_b

pilo content-promote

assert_file_exists /$STATIC/$archive_a/$a
assert_file_exists /$STATIC/$archive_b/$b
