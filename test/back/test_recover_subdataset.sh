#!/bin/sh
set -e

snap=baseline

echo data > /$ADMIN/file.txt
pilo storage-snapshot $snap
pilo storage-replica-seed
clear_holds $ADMIN
zfs destroy -r $ADMIN

pilo storage-recover $ADMIN >/dev/null

zfs list -t snapshot | assert_grep "$ADMIN@$snap"
