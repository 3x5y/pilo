#!/bin/sh
set -e

FILE=file.txt
PILE=/tank/data/active/pile-readonly

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

system-static-promote in/$FILE collection

cat $PILE/.manifest

if grep -q "./in/$FILE$" $PILE/.manifest
then
    fail "file still present in pile manifest"
fi
