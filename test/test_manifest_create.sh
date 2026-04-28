#!/bin/sh
set -e

file=test.txt
mkfile hello $file
capture_file $file
system-ingest-pile
system-manifest-update

assert_manifest_valid /$PILE
