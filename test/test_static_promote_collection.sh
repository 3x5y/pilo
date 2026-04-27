#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly
DST=tank/data/static/collection

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection/$FILE

system-static-promote

assert_file_exists /$DST/$FILE
assert_not_exists /$PILE/out/collection/$FILE
