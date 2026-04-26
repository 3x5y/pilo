#!/bin/sh
set -e

# tests ZFS instead of system commands for unknown reason?

SRC=tank/data/active/admin
FILE=/$SRC/recovery_test.txt

echo recover me > $FILE
SNAP=$SRC@recovery_test
zfs snapshot $SNAP
rm $FILE
assert_not_exists $FILE

zfs rollback $SNAP
assert_file_exists $FILE
