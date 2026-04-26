#!/bin/sh
set -e

SRC=$TEST_ROOT/active
DST=$TEST_REPLICA/data/active

echo hello > /$SRC/admin/file.txt
system-snapshot t0

system-replicate

zfs list -t snapshot | assert_grep $DST@t0
assert_file_exists /$DST/admin/.zfs/snapshot/t0/file.txt
