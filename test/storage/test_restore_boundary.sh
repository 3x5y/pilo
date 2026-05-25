#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
file=file.txt
temp=temp.txt
snap=baseline
echo admin > /$ADMIN/$file
zfs create -p $STASH
echo temp > /$STASH/$temp
pilo storage-snapshot $snap
pilo storage-replica-seed
clear_holds $ADMIN
clear_holds $STASH
zfs destroy -r $ADMIN
zfs destroy -r $STASH

pilo storage-restore $repl $ADMIN $snap

assert_grep admin < /$ADMIN/.zfs/snapshot/$snap/$file
assert_not_exists /$STASH/$temp
