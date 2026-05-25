#!/bin/sh
set -e

file=test.txt
mkfile hello $file
capture_file $file
pilo content-ingest

assert_manifest_valid pile /$PILE
