#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

system-snapshot test_snap

assert_file_exists /$PILE/.zfs/snapshot/test_snap/in/$FILE
