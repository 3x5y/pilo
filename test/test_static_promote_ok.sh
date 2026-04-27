#!/bin/sh
set -e

SRC=/tank/data/active/pile-readonly
DST=/tank/data/static/collection

echo x > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
#system-manifest-update # FIXME

system-static-promote in/file.txt collection

assert_not_exists $SRC/file.txt "file still in pile"
assert_file_exists $DST/file.txt "file not moved to filing"
