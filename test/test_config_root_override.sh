#!/bin/sh
set -e

alt_root=tank/test-alt

file=file.txt
zfs destroy -r $alt_root 2>/dev/null || true
zfs create -p $alt_root/active/pile-intake

export SYSTEM_ROOT=$alt_root
system-init
mkfile data $file
system-capture $TMP/$file

assert_file_exists /$alt_root/active/pile-intake/$file
assert_not_exists /$PILE/$file
