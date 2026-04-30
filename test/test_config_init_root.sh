#!/bin/sh
set -e

alt_root=tank/test-alt
pile=$alt_root/active/pile-readonly

zfs destroy -r $alt_root 2>/dev/null || true
zfs create -p $alt_root/active/pile-intake
zfs create -p $alt_root/active/pile-readonly
zfs create -p $alt_root/active/admin
zfs create -p $alt_root/stash
zfs create -p $alt_root/static/collection

export SYSTEM_ROOT=$alt_root

system-init

assert_dir_exists /$pile/in
assert_dir_exists /$pile/out/collection
[ $(zfs get -H -o value readonly $pile) = on ] \
    || fail $pile not readonly after init
