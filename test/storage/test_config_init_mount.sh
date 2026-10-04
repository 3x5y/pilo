#!/bin/sh
set -eu

reset_system tank/test/test-alt /alter

assert_dir_exists $PILO_PATH/pile/in
assert_dir_exists $PILO_PATH/pile/out/collection
[ $(zfs get -H -o value readonly $COLLECTION) = on ] \
    || fail $COLLECTION not readonly after init
[ "$(zfs get -H -o value canmount $COLLECTION)" = on ] \
    || fail "pile canmount incorrect"
[ "$(zfs get -H -o value mountpoint $COLLECTION)" = "$PILO_PATH/static/collection" ] \
    || fail "pile mountpoint incorrect"
