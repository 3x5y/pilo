#!/bin/sh
set -e

repl=$TEST_REPLICA/admin
file=file.txt
temp=temp.txt
snap=baseline
echo admin > /$ADMIN/$file
#zfs create -p $RSYNC
echo temp > /$RSYNC/$temp
pilo storage-snapshot $snap
pilo storage-replica-seed
clear_holds $ADMIN
clear_holds $RSYNC
zfs destroy -r $ADMIN
zfs destroy -r $RSYNC

pilo storage-restore $repl $ADMIN $snap
zfs set mountpoint=/$ADMIN $ADMIN

assert_grep admin < /$ADMIN/.zfs/snapshot/$snap/$file
assert_not_exists /$RSYNC/$temp
