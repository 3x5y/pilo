#!/bin/sh
set -e

file=nice.txt
mkfile data $file
capture_file $file
pilo ingest-pile
pilo rewrite "$(printf "mv\tin/$file\tout/collection/$file")"

pilo static-promote

manifest=$PILO_ADMIN_PATH/manifest/pile.manifest
cat $manifest
assert_not_grep "./in/$file$" < $manifest
