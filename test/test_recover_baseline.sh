#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
file=important.txt
snap=baseline
echo important > /$ADMIN/$file
system-snapshot $snap
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $repl $ADMIN $snap >/dev/null

assert_grep important < /$ADMIN/.zfs/snapshot/$snap/$file
