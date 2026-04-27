#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
DST=tank/data/static/filing/2025

zfs create -p $DST

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

with_writable $PILE mkdir -p /$PILE/out/filing/2025/a/b
with_writable $PILE mv /$PILE/in/file.txt /$PILE/out/filing/2025/a/b/file.txt

system-static-promote

assert_file_exists /$DST/a/b/file.txt
