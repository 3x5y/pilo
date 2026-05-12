#!/bin/sh
set -e

file=test.txt
mkfile hello $file
capture_file $file
pilo ingest-pile

assert_manifest_valid pile /$PILE
