#!/bin/sh
set -e

FILE="/tank/data/active/pile/recovery_test.txt"

echo "recover me" > "$FILE"

SNAP="tank/data/active/pile@recovery_test"
zfs snapshot "$SNAP"

rm "$FILE"

if [ -f "$FILE" ]
then
    echo "FAIL: file not deleted"
    exit 1
fi

zfs rollback "$SNAP"

if [ ! -f "$FILE" ]
then
    echo "FAIL: file not restored after rollback"
    exit 1
fi
