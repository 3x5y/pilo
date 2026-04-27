#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

with_writable $PILE \
    mkdir -p /$PILE/out/collection/a/b
with_writable $PILE \
    mv /$PILE/in/file.txt /$PILE/out/collection/a/b/file.txt

system-static-promote

grep -q " \./collection/a/b/file.txt$" /tank/data/static/.manifest \
    || fail "missing preserved path in manifest"
