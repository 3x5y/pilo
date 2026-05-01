#!/bin/sh
set -e

file=test.txt
mkfile hello $file
capture_file $file
pilo ingest-pile
pilo manifest-update

assert_manifest_valid /$PILE
