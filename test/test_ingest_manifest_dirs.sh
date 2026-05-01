#!/bin/sh
set -e

file=foo/bar/file.txt
mkintake data $file

pilo ingest-pile

assert_manifest_entry /$PILE " \./in/$file$"
assert_manifest_valid /$PILE
