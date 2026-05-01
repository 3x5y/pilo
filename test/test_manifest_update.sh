#!/bin/sh
set -e

mkfile data file1.txt
capture_file file1.txt
pilo-ingest-pile
pilo-manifest-update

mkfile another file2.txt
capture_file file2.txt
pilo-ingest-pile

pilo-manifest-update

assert_manifest_valid /$PILE
