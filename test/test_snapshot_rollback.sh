#!/bin/sh
set -eu

# tests ZFS instead of system commands for unknown reason?

path=$ADMIN_PATH/recovery_test.txt
echo recover-me > $path
snap=$ADMIN@recovery_test
zfs snapshot $snap
rm $path
assert_not_exists $path

zfs rollback $snap

assert_file_exists $path
assert_grep recover-me < $path
