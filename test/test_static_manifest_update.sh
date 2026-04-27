#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
DST=/tank/data/static/collection

echo important > /tmp/item.txt
system-capture /tmp/item.txt
system-ingest-pile

system-manifest-update

with_writable $PILE \
    mv /$PILE/in/item.txt /$PILE/out/collection/item.txt
system-static-promote

#assert_grep item.txt < $DST/.manifest
