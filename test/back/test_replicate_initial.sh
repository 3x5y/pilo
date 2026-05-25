#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin

echo hello > /$ADMIN/file.txt
pilo storage-snapshot t0
pilo storage-replica-seed

zfs list -t snapshot | assert_grep $repl@t0
zfs set canmount=on $repl
zfs set mountpoint=/$repl $repl
assert_file_exists /$repl/.zfs/snapshot/t0/file.txt
