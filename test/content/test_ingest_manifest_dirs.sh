#!/bin/sh
set -e

file=foo/bar/file.txt
mkintake data $file

pilo content-ingest

assert_manifest_entry pile " \./in/$file$"
assert_manifest_valid pile /$PILE
