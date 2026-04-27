#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly
DST=tank/data/static/filing/2025

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

with_writable $PILE \
    mkdir -p /$PILE/out/filing/2025

with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/filing/2025/$FILE

system-static-promote

assert_file_exists /$DST/$FILE
assert_not_exists /$PILE/out/filing/2025/$FILE
