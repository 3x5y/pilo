#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
file=repl.txt

echo v1 > /$ADMIN/$file
pilo storage-snapshot t0
pilo storage-replica-seed

echo v2 > /$ADMIN/$file
pilo storage-snapshot t1
pilo storage-replicate

zfs list -t snapshot | assert_grep $repl@t1
zfs set canmount=on $repl
zfs set mountpoint=/$repl $repl
assert_grep v2 < /$repl/.zfs/snapshot/t1/$file
