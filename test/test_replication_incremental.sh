#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile
DST=$TEST_REPLICA/pile

echo v1 > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t0
zfs send $SRC@t0 | zfs receive $DST

echo v2 > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t1
zfs send -i $SRC@t0 $SRC@t1 | zfs receive $DST

zfs list -t snapshot | assert_grep $DST@t1
assert_grep v2 < /$DST/.zfs/snapshot/t1/file.txt
