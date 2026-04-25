#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile
DST=$TEST_REPLICA/pile

echo data > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t0

system-replicate
system-replicate

zfs list -t snapshot | assert_grep $DST@t0

COUNT=$(zfs list -t snapshot | grep "$DST@" | wc -l)
[ "$COUNT" -eq 1 ] || fail "replication not idempotent"
