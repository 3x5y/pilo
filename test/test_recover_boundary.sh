#!/bin/sh
set -e

admin=$ACTIVE/admin
repl=$TEST_REPLICA/active/admin
file=file.txt
temp=temp.txt
snap=baseline
echo admin > /$admin/$file
echo temp > /$STASH/$temp
system-snapshot $snap
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $repl $admin $snap >/dev/null

assert_grep admin < /$admin/.zfs/snapshot/$snap/$file
assert_not_exists /$STASH/$temp
