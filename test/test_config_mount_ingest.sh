#!/bin/sh
set -e

alt_root=tank/test-alt
alt_mount=/alt-mount

zfs destroy -r $alt_root 2>/dev/null || true
zfs create -o mountpoint=$alt_mount $alt_root
init_system $alt_root $alt_mount

file=root-override.txt
mkfile data $file
capture_file $file
system-ingest-pile

assert_file_exists $alt_mount/active/pile-readonly/in/$file
assert_not_exists /$TEST_ROOT/active/pile-readonly/in/$file

