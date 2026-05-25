#!/bin/sh
set -e

file=nice.txt
mkfile data $file
capture_file $file
pilo content-ingest
printf "mv\tin/$file\tout/collection/$file" \
    | pilo rewrite

pilo content-promote

manifest=$PILO_ADMIN_PATH/manifest/pile.manifest
cat $manifest
assert_not_grep "./in/$file$" < $manifest
