#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
system-ingest-pile

system-snapshot test_snap

assert_file_exists /$PILE/.zfs/snapshot/test_snap/in/$file
