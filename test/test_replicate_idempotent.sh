#!/bin/sh
set -e

echo data > /$ACTIVE/admin/file.txt
system-snapshot t0

system-replicate
system-replicate

zfs list -t snapshot | assert_grep $ACTIVE@t0
count=$(zfs list -t snapshot | grep $ACTIVE@ | wc -l)
[ $count -eq 1 ] || fail replication not idempotent
