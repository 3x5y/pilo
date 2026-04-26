#!/bin/sh
set -e

SRC=$TEST_ROOT/active
DST=$TEST_REPLICA/data/active

echo data > /$SRC/admin/file.txt
system-snapshot t0

system-replicate
system-replicate

zfs list -t snapshot | assert_grep $DST@t0
COUNT=$(zfs list -t snapshot | grep $DST@ | wc -l)
[ $COUNT -eq 1 ] || fail replication not idempotent
