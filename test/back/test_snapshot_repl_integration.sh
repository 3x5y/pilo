#!/bin/sh
set -e

repl_admin=$TEST_REPLICA/active/admin

echo v1 > $ADMIN_PATH/file.txt
pilo snapshot-incr
pilo replica-seed

echo v2 > $ADMIN_PATH/file.txt
pilo snapshot-incr
pilo replicate

echo v3 > $ADMIN_PATH/file.txt
pilo snapshot-incr
pilo replicate

snap=$(zfs list -t snap -s creation -Ho name "$repl_admin" \
        | tail -n1 | cut -d@ -f2)

zfs set canmount=on $repl_admin
zfs inherit mountpoint $REPLICA_ROOT
zfs inherit mountpoint $TEST_REPLICA
assert_grep v3 < /$repl_admin/.zfs/snapshot/$snap/file.txt
