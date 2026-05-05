#!/bin/sh
set -e

pilo snapshot t0
pilo replicate

pilo snapshot t1
pilo replicate

for ds in \
    $TEST_REPLICA/active/admin \
    $TEST_REPLICA/static
do
    [ "$(zfs get -H -o value readonly $ds)" = on ] \
        || fail "$ds not readonly"
done