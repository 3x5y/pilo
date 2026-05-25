#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot t1
pilo storage-replicate

for ds in \
    $TEST_REPLICA/active/admin \
    $TEST_REPLICA/static
do
    [ "$(zfs get -H -o value readonly $ds)" = on ] \
        || fail "$ds not readonly"
done
