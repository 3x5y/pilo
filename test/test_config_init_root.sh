#!/bin/sh
set -eu

init_system tank/test/test-alt

assert_dir_exists $PILE_PATH/in
assert_dir_exists $PILE_PATH/out/collection
[ $(zfs get -H -o value readonly $PILE) = on ] \
    || fail $PILE not readonly after init
