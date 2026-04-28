#!/bin/sh
set -e

system-snapshot-anchor
system-replicate

echo data > /$ACTIVE/admin/file.txt

system-snapshot-rpo
system-replicate

zfs list -t snapshot $TEST_REPLICA | assert_grep "$TEST_REPLICA@r-"
for f in /$TEST_REPLICA/active/admin/.zfs/snapshot/*/file.txt
do
    assert_grep data < $f
done
