#!/bin/sh
set -e

alt_root=$TEST_ROOT/test-alt
pile=$alt_root/active/pile-readonly

zfs destroy -r $alt_root 2>/dev/null || true
zfs create $alt_root
init_datasets $alt_root

export SYSTEM_ROOT=$alt_root
export SYSTEM_PATH=/$alt_root
system-init

assert_dir_exists /$pile/in
assert_dir_exists /$pile/out/collection
[ $(zfs get -H -o value readonly $pile) = on ] \
    || fail $pile not readonly after init
