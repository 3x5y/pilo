#!/bin/sh
set -e

FILE=/tank/data/active/pile/recovery_test.txt

echo recover me > $FILE

SNAP=tank/data/active/pile@recovery_test
zfs snapshot $SNAP

rm $FILE

assert_not_exists $FILE

zfs rollback $SNAP

assert_file_exists $FILE
