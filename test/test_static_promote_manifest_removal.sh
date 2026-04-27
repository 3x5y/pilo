#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection
system-static-promote

cat /$PILE/.manifest

if grep -q "./in/$FILE$" /$PILE/.manifest
then
    fail "file still present in pile manifest"
fi
