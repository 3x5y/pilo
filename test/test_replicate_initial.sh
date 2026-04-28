#!/bin/sh
set -e

admin=$ACTIVE/admin
repl=$TEST_REPLICA/admin

echo hello > /$admin/file.txt
zfs snapshot $admin@t0

system-replicate $admin $repl

zfs list -t snapshot | assert_grep $repl@t0
assert_file_exists /$repl/.zfs/snapshot/t0/file.txt
