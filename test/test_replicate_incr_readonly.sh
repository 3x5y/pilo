#!/bin/sh
set -e

admin=$ACTIVE/admin
repl=$TEST_REPLICA_ROOT/admin

zfs snapshot $admin@t0
system-replicate $admin $repl

zfs snapshot $admin@t1
system-replicate $admin $repl

[ $(zfs get -H -o value readonly $repl) = on ] \
    || fail $repl not readonly after incremental replication
