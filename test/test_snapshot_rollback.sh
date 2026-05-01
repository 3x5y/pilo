#!/bin/sh
set -e

# tests ZFS instead of system commands for unknown reason?

path=/$ADMIN/recovery_test.txt
echo recover-me > $path
snap=$ADMIN@recovery_test
zfs snapshot $snap
rm $path
assert_not_exists $path

zfs rollback $snap

assert_file_exists $path
assert_grep recover-me < $path
