#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
DST=/tank/data/static/collection
FILE=file.txt

echo x > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection
system-static-promote

assert_not_exists /$PILE/out/collection/$FILE "file still in pile"
assert_file_exists $DST/file.txt "file not moved to filing"
