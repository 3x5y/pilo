#!/bin/sh
set -eu

alt=tank/test/test-alt
init_system $alt

assert_dir_exists $PILE_PATH/in
assert_dir_exists $PILE_PATH/out/collection
[ $(zfs get -H -o value readonly $PILE) = on ] \
    || fail $PILE not readonly after init
