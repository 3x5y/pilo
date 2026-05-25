#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
pilo content-ingest

pilo storage-snapshot test_snap

assert_file_exists /$PILE/.zfs/snapshot/test_snap/in/$file
