#!/bin/sh
set -e

repl_static=$TEST_REPLICA/static

system-snapshot t0
system-replicate

system-snapshot t1
system-replicate

[ $(zfs get -H -o value readonly $TEST_REPLICA/active/admin) = on ] \
    || fail $repl not readonly after incremental replication
[ $(zfs get -H -o value readonly $TEST_REPLICA/static) = on ] \
    || fail $repl not readonly after incremental replication
