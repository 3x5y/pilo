#!/bin/sh
set -e

SRC=tank/data/active/pile-readonly
FILE=/$SRC/recovery_test.txt

echo recover me > $FILE
SNAP=$SRC@recovery_test
zfs snapshot $SNAP
rm $FILE
assert_not_exists $FILE

zfs rollback $SNAP
assert_file_exists $FILE
