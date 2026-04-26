#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

zfs snapshot $PILE@test_snap

assert_file_exists /$PILE/.zfs/snapshot/test_snap/$FILE
