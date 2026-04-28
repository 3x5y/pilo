#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
system-ingest-pile

# NB tabs!!
system-rewrite "mv	in/$file	sort/$file"
system-rewrite "mv	in/$file	sort/$file" >/dev/null || true

assert_file_exists /$PILE/sort/$file
assert_manifest_valid /$PILE
