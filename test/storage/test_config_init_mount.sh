#!/bin/sh
set -eu

reset_system tank/test/test-alt /alter

assert_dir_exists $PILE_PATH/in
assert_dir_exists $PILE_PATH/out/collection
[ $(zfs get -H -o value readonly $PILE) = on ] \
    || fail $PILE not readonly after init
[ "$(zfs get -H -o value canmount $PILE)" = on ] \
    || fail "pile canmount incorrect"
[ "$(zfs get -H -o value mountpoint $PILE)" = "$PILE_PATH" ] \
    || fail "pile mountpoint incorrect"
