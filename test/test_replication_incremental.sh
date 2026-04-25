#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile
DST=$TEST_REPLICA/pile

echo v1 > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t0
system-replicate

echo v2 > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t1
system-replicate

zfs list -t snapshot | assert_grep $DST@t1
assert_grep v2 < /$DST/.zfs/snapshot/t1/file.txt
