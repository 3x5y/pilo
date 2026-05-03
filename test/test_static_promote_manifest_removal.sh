#!/bin/sh
set -e

file=nice.txt
mkfile data $file
capture_file $file
pilo ingest-pile

with_writable $PILE \
    mv /$PILE/in/$file /$PILE/out/collection
pilo static-promote

manifest=$PILO_ADMIN_PATH/manifest/pile.manifest
cat $manifest
assert_not_grep "./in/$file$" < $manifest
