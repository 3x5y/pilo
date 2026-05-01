#!/bin/sh
set -e

repl=$REPLICA_ROOT/admin

zfs snapshot $ADMIN@t0
system-replicate $ADMIN $repl

zfs snapshot $ADMIN@t1
system-replicate $ADMIN $repl

[ $(zfs get -H -o value readonly $repl) = on ] \
    || fail $repl not readonly after incremental replication
