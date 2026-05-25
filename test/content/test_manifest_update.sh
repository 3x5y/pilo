#!/bin/sh
set -e

mkfile data file1.txt
capture_file file1.txt
pilo content-ingest

mkfile another file2.txt
capture_file file2.txt
pilo content-ingest

assert_manifest_valid pile /$PILE
