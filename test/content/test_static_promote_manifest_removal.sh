#!/bin/sh
set -e

file=nice.txt
echo data > /$PILE/out/collection/$file
create_pile_manifest

pilo content-promote

manifest=/$ADMIN/manifest/pile.manifest
cat $manifest
assert_not_grep "./out/collection/$file$" < $manifest
