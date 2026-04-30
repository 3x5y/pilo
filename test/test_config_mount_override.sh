#!/bin/sh
set -e

exit 0

alt_root=tank/test-alt
alt_path=$TMP/root
zfs destroy -r $alt_root 2>/dev/null || true
zfs create -p $alt_root

export SYSTEM_ROOT=$alt_root
export SYSTEM_PATH=$alt_mount
system-init
file=file.txt
mkfile data $file
system-capture $TMP/$file

assert_file_exists $alt_path/active/pile-intake/$file
assert_not_exists $alt_path/$file

