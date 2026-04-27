#!/bin/sh
set -e

FILE=file.txt
SRC=/tank/data/active/pile-readonly/$FILE
DST=/tank/data/static/collection/$FILE

echo good > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

system-static-promote in/$FILE collection

# verify integrity via checksum
cmp "$SRC" "$DST" 2>/dev/null && fail "source should be removed"

(cd /tank/data/static/collection && sha256sum --quiet --strict -c .manifest)
