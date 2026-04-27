#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly
SRC=/$PILE/in/$FILE
DST=/tank/data/static/collection/$FILE

echo good > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

with_writable $PILE \
    mv $SRC /$PILE/out/collection

system-static-promote

# verify integrity via checksum
cmp "$SRC" "$DST" 2>/dev/null && fail "source should be removed"

(cd /tank/data/static && sha256sum --quiet --strict -c .manifest)
