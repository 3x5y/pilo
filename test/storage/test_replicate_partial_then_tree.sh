#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
file=repl.txt

echo v0 > /$ADMIN/$file
pilo storage-snapshot t0
pilo storage-replica-seed

echo v1 > /$ADMIN/$file
pilo storage-snapshot t1
pilo storage-replicate $ADMIN $repl

echo v2 > /$ADMIN/$file
pilo storage-snapshot t2

capture_status pilo storage-replicate

assert_command_ok
zfs list -t snapshot | assert_grep $repl@t2
zfs set canmount=on $repl
zfs set mountpoint=/$repl $repl
assert_grep v2 < /$repl/.zfs/snapshot/t2/$file


