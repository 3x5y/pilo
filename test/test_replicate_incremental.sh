#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly
DST=$TEST_REPLICA/pile-readonly

echo v1 > /$SRC/file.txt
zfs snapshot $SRC@t0
system-replicate

echo v2 > /$SRC/file.txt
zfs snapshot $SRC@t1
system-replicate

zfs list -t snapshot | assert_grep $DST@t1
assert_grep v2 < /$DST/.zfs/snapshot/t1/file.txt
