#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo content-ingest

printf "mv\tin/file.txt\tout/collection/file.txt" \
    | pilo content-reorg

pilo content-promote

assert_owner $PILO_USER /"$STATIC"/collection/file.txt
