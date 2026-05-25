#!/bin/sh
set -e

file=file.txt
mkfile data $file
capture_file $file
pilo content-ingest

# reorganise
pilo content-reorg "mv	in/$file	sort/$file"

manifest="$PILO_ADMIN_PATH"/manifest/pile.manifest
assert_grep " \./sort/$file$" < $manifest
assert_not_grep " \./in/$file$" < $manifest
assert_manifest_valid pile /$PILE
