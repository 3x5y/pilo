#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo content-ingest

printf "mv\tin/file.txt\tout/collection/file.txt" \
    | pilo content-reorg

pilo content-promote


# corrupt static file
with_writable $COLLECTION \
    sh -c "echo bad > /'$COLLECTION'/file.txt"

capture_status pilo manifest-verify
assert_command_fail
