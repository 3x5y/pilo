#!/bin/sh
set -e

repl=$REPLICA_ROOT/admin
file=repl.txt

echo v1 > /$ADMIN/$file
zfs snapshot $ADMIN@t0
pilo replicate $ADMIN $repl

echo v2 > /$ADMIN/$file
zfs snapshot $ADMIN@t1
pilo replicate $ADMIN $repl

zfs list -t snapshot | assert_grep $repl@t1
zfs inherit mountpoint $REPLICA_ROOT
assert_grep v2 < /$repl/.zfs/snapshot/t1/$file
