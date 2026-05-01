#!/bin/sh
set -e

repl_static=$TEST_REPLICA/static

pilo-snapshot t0
pilo-replicate

pilo-snapshot t1
pilo-replicate

[ $(zfs get -H -o value readonly $TEST_REPLICA/active/admin) = on ] \
    || fail $repl not readonly after incremental replication
[ $(zfs get -H -o value readonly $TEST_REPLICA/static) = on ] \
    || fail $repl not readonly after incremental replication
