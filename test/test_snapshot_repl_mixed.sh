#!/bin/sh
set -e

admin=/$ACTIVE/admin
repl_admin=$TEST_REPLICA/active/admin

echo v1 > /$admin/file.txt
system-snapshot-anchor
system-replicate

echo v2 > /$admin/file.txt
system-snapshot-rpo
system-replicate

echo v3 > /$admin/file.txt
system-snapshot-anchor
system-replicate

snap=$(zfs list -t snap -s creation -Ho name "$repl_admin" \
        | tail -n1 | cut -d@ -f2)

assert_grep v3 < /$repl_admin/.zfs/snapshot/$snap/file.txt
