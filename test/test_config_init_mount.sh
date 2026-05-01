#!/bin/sh
set -eu

mount=/alter
init_system tank/test/test-alt $mount

assert_dir_exists $PILE_PATH/in
assert_dir_exists $PILE_PATH/out/collection
[ $(zfs get -H -o value readonly $PILE) = on ] \
    || fail $PILE not readonly after init
