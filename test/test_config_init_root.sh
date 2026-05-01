#!/bin/sh
set -e

alt_root=$TEST_ROOT/test-alt
pile=$alt_root/active/pile-readonly

zfs destroy -r $alt_root 2>/dev/null || true
zfs create $alt_root
init_system $alt_root /$alt_root

assert_dir_exists /$pile/in
assert_dir_exists /$pile/out/collection
[ $(zfs get -H -o value readonly $pile) = on ] \
    || fail $pile not readonly after init
