#!/bin/sh
set -e

file=file.txt
dir=a/b
mkdir -p /$PILE/out/collection/$dir
echo data > /$PILE/out/collection/$dir/$file
create_pile_manifest

pilo content-promote

assert_manifest_entry collection " \./$dir/$file$"
