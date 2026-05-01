#!/bin/sh
set -e

repl_admin=$TEST_REPLICA/active/admin

echo v1 > $ADMIN_PATH/file.txt
system-snapshot-anchor
system-replicate

echo v2 > $ADMIN_PATH/file.txt
system-snapshot-rpo
system-replicate

echo v3 > $ADMIN_PATH/file.txt
system-snapshot-anchor
system-replicate

snap=$(zfs list -t snap -s creation -Ho name "$repl_admin" \
        | tail -n1 | cut -d@ -f2)

zfs inherit mountpoint $REPLICA_ROOT
assert_grep v3 < /$repl_admin/.zfs/snapshot/$snap/file.txt
