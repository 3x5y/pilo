#!/bin/sh
set -e

alt_root=$TEST_ROOT/alt
alt_mount=/alt-mount
pile=$alt_mount/active/pile-readonly

zfs destroy -r $alt_root 2>/dev/null || true
zfs create -o mountpoint=$alt_mount $alt_root

export SYSTEM_ROOT=$alt_root
export SYSTEM_PATH=$alt_mount
system-init

assert_dir_exists $pile/in
assert_dir_exists $pile/out/collection
[ $(zfs get -H -o value readonly $pile) = on ] \
    || fail $pile not readonly after init
