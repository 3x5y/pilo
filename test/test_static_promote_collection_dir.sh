#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
DST=tank/data/static/collection

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

with_writable $PILE mkdir -p /$PILE/out/collection/foo/bar
with_writable $PILE mv /$PILE/in/file.txt /$PILE/out/collection/foo/bar/file.txt

system-static-promote

assert_file_exists /$DST/foo/bar/file.txt
assert_not_exists /$PILE/out/collection/foo/bar/file.txt
