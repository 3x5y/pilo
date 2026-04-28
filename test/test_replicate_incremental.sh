#!/bin/sh
set -e

admin=$ACTIVE/admin
repl=$TEST_REPLICA/admin
file=repl.txt

echo v1 > /$admin/$file
zfs snapshot $admin@t0
system-replicate $admin $repl

echo v2 > /$admin/$file
zfs snapshot $admin@t1
system-replicate $admin $repl

zfs list -t snapshot | assert_grep $repl@t1
assert_grep v2 < /$repl/.zfs/snapshot/t1/$file
