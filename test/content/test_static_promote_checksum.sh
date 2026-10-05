#!/bin/sh
set -e


file=good-file.txt
echo good > /$PILE/out/collection/$file
create_pile_manifest

pilo content-promote

assert_manifest_entry collection " \./$file$"
assert_manifest_valid collection /$COLLECTION
