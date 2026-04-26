#!/bin/sh
set -e

SRC=$TEST_ROOT/active
DST=$TEST_REPLICA/active

echo v1 > /$SRC/admin/file.txt
system-snapshot t0
system-replicate

echo v2 > /$SRC/admin/file.txt
system-snapshot t1
system-replicate

zfs list -t snapshot | assert_grep $DST@t1
assert_grep v2 < /$DST/admin/.zfs/snapshot/t1/file.txt
