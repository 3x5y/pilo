#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
file=file.txt
temp=temp.txt
snap=baseline
echo admin > /$ADMIN/$file
zfs create -p $STASH
echo temp > /$STASH/$temp
pilo snapshot $snap
pilo replicate
zfs destroy -r $ADMIN
zfs destroy -r $STASH

pilo recover-baseline $repl $ADMIN $snap >/dev/null

assert_grep admin < /$ADMIN/.zfs/snapshot/$snap/$file
assert_not_exists /$STASH/$temp
