#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
DATASET=tank/data/static/filing/1990-2000

zfs create -p -o readonly=on $DATASET

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

with_writable $PILE \
    mkdir -p /$PILE/out/filing/1990-2000

with_writable $PILE \
    mv /$PILE/in/file.txt /$PILE/out/filing/1990-2000/file.txt

system-static-promote

assert_file_exists /tank/data/static/filing/1990-2000/file.txt
