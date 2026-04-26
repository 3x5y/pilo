#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly
DST=$TEST_REPLICA/pile-readonly

echo hello > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
zfs snapshot $SRC@t0

system-replicate

zfs list -t snapshot | assert_grep $DST@t0
assert_file_exists /$DST/.zfs/snapshot/t0/file.txt
