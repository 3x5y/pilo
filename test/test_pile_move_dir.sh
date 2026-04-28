#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
system-ingest-pile

system-rewrite "mv in/$file sort/2025/a/$file"

assert_file_exists /$PILE/sort/2025/a/$file
assert_not_exists /$PILE/in/$file
assert_manifest_valid /$PILE
