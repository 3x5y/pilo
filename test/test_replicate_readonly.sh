#!/bin/sh
set -e

repl=$REPLICA_ROOT/admin

zfs snapshot $ADMIN@t0

pilo-replicate $ADMIN $repl

[ $(zfs get -H -o value readonly $repl) = on ] \
    || fail $repl not readonly after initial replication
