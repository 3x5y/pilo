#!/bin/sh
set -e

pilein=pile-in.txt
coldir=a/b
fildir=c/d
colfile=previous-col.txt
filfile=previous-fil.txt
colpromote=promote-col.txt
filpromote=promote-fil.txt
archive=2025
mkdir -p /$PILE/out/collection/$coldir
mkdir -p /$PILE/out/filing/$archive/$fildir
echo pile-in > /$PILE/in/$pilein
echo promote-col > /$PILE/out/collection/$coldir/$colpromote
echo promote-fil > /$PILE/out/filing/$archive/$fildir/$filpromote
zfs create -p -o readonly=on $FILING/$archive
with_writable $COLLECTION \
    mkdir -p /$COLLECTION/$coldir
with_writable $COLLECTION \
    sh -c "echo previous-col > '/$COLLECTION/$coldir/$colfile'"
with_writable $FILING/$archive \
    mkdir -p /$FILING/$archive/$fildir
with_writable $FILING/$archive \
    sh -c "echo previous-fil > '/$FILING/$archive/$fildir/$filfile'"

init_manifest
create_manifest pile /$PILE
create_manifest collection /$COLLECTION
create_manifest filing /$FILING
runuser git -C /$ADMIN/manifest add *.manifest
runuser git -C /$ADMIN/manifest commit -m 'initial'

pilo content-promote

assert_manifest_valid pile /$PILE
assert_manifest_valid collection /$COLLECTION
assert_manifest_valid filing /$FILING
assert_manifest_entry pile " \./in/$pilein$"
assert_manifest_entry collection " \./$coldir/$colfile$"
assert_manifest_entry collection " \./$coldir/$colpromote$"
assert_manifest_entry filing " \./$archive/$fildir/$filfile$"
assert_manifest_entry filing " \./$archive/$fildir/$filpromote$"
manifest=/$ADMIN/manifest/pile.manifest
assert_not_grep "./out/collection$coldir/$colpromote$" < $manifest
assert_not_grep "./out/filing/$archive/$fildie/$filpromote$" < $manifest
