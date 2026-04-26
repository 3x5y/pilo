#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly
DST=$TEST_REPLICA/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
zfs snapshot $SRC@t0

system-replicate
system-replicate

zfs list -t snapshot | assert_grep $DST@t0

COUNT=$(zfs list -t snapshot | grep $DST@ | wc -l)
[ $COUNT -eq 1 ] || fail replication not idempotent
