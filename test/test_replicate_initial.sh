#!/bin/sh
set -e

SRC=$TEST_ROOT/active/admin
DST=$TEST_REPLICA/admin

echo hello > /$SRC/file.txt
zfs snapshot $SRC@t0

system-replicate $SRC $DST

zfs list -t snapshot | assert_grep $DST@t0
assert_file_exists /$DST/.zfs/snapshot/t0/file.txt
