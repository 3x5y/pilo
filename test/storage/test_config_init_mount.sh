#!/bin/sh
set -eu

reset_system tank/test/test-alt /alter

assert_dir_exists $PILO_PATH/pile/in
assert_dir_exists $PILO_PATH/pile/out/collection
[ $(zfs get -H -o value readonly $PILE) = on ] \
    || fail $PILE not readonly after init
[ "$(zfs get -H -o value canmount $PILE)" = on ] \
    || fail "pile canmount incorrect"
[ "$(zfs get -H -o value mountpoint $PILE)" = "$PILO_PATH/pile" ] \
    || fail "pile mountpoint incorrect"
