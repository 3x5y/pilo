#!/bin/sh
set -e

repl=$REPLICA_ROOT/admin

echo hello > /$ADMIN/file.txt
zfs snapshot $ADMIN@t0

pilo-replicate $ADMIN $repl

zfs list -t snapshot | assert_grep $repl@t0
zfs inherit mountpoint $REPLICA_ROOT
assert_file_exists /$repl/.zfs/snapshot/t0/file.txt
