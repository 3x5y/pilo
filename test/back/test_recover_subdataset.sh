#!/bin/sh
set -e

snap=baseline

echo data > /$ADMIN/file.txt
pilo snapshot $snap
pilo replica-seed
zfs destroy -r $ADMIN

pilo recover $ADMIN >/dev/null

zfs list -t snapshot | assert_grep "$ADMIN@$snap"
