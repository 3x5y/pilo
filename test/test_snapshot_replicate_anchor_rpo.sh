#!/bin/sh
set -e

system-snapshot-anchor
system-replicate

echo data > /$ADMIN/file.txt

system-snapshot-rpo
snap=$(zfs list -t snap -Ho name $TEST_ROOT | grep @r- | cut -d@ -f2)
system-replicate

zfs list -t snapshot $TEST_REPLICA | assert_grep "$TEST_REPLICA@r-"
zfs inherit mountpoint $REPLICA_ROOT
assert_grep data < /$TEST_REPLICA/active/admin/.zfs/snapshot/$snap/file.txt
