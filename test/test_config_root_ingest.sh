#!/bin/sh
set -e

altroot=tank/test-alt

zfs destroy -r $altroot 2>/dev/null || true
zfs create $altroot

export SYSTEM_ROOT=$altroot
export SYSTEM_PATH=/$altroot
system-init
file=root-override.txt
mkfile data $file
capture_file $file
system-ingest-pile

assert_file_exists /$altroot/active/pile-readonly/in/$file
assert_not_exists /$TEST_ROOT/active/pile-readonly/in/$file
