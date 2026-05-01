#!/bin/sh
set -e

alt_root=tank/test-alt
alt_path=/alt-mount
zfs destroy -r $alt_root 2>/dev/null || true
zfs create -p -o mountpoint=$alt_path $alt_root
init_system $alt_root $alt_path

file=file.txt
mkfile data $file
capture_file $file

assert_file_exists $alt_path/active/pile-intake/$file
assert_not_exists $alt_path/$file

