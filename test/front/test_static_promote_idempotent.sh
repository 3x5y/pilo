#!/bin/sh
set -e

file=file.txt
dst=collection/a
mkfile data $file
capture_file $file
pilo ingest-pile
printf "mv\tin/$file\tout/$dst/$file" \
    | pilo rewrite
pilo static-promote
# reintroduce identical
mkfile data $file
capture_file $file
pilo ingest-pile
printf "mv\tin/$file\tout/$dst/$file" \
    | pilo rewrite

pilo static-promote

assert_file_exists /$STATIC/$dst/$file
assert_not_exists /$PILE/out/$dst/$file
