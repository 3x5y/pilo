#!/bin/sh
set -e

SRC=$TEST_ROOT/active
DST=$TEST_REPLICA/active

echo data > /$SRC/admin/file.txt
zfs snapshot -r $SRC@t0

system-replicate $SRC $DST
system-replicate $SRC $DST

zfs list -t snapshot | assert_grep $DST@t0
COUNT=$(zfs list -t snapshot | grep $DST@ | wc -l)
[ $COUNT -eq 1 ] || fail replication not idempotent
