#!/bin/sh
set -e

admin=$ACTIVE/admin
repl=$TEST_REPLICA/active/admin
file=important.txt
snap=baseline
echo important > /$admin/$file
system-snapshot $snap
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $repl $admin $snap >/dev/null

assert_grep important < /$admin/.zfs/snapshot/$snap/$file
