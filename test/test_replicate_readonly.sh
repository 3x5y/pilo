#!/bin/sh
set -e

repl=$TEST_REPLICA_ROOT/admin

zfs snapshot $ADMIN@t0

system-replicate $ADMIN $repl

[ $(zfs get -H -o value readonly $repl) = on ] \
    || fail $repl not readonly after initial replication
