#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile
DST=$TEST_REPLICA/pile

echo hello > /tank/data/active/pile/file1.txt
zfs snapshot $SRC@t0

system-replicate

zfs list -t snapshot | assert_grep $DST@t0
assert_file_exists /$DST/.zfs/snapshot/t0/file1.txt
