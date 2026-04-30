#!/bin/sh
set -e

altroot=tank/test-alt

zfs destroy -r $altroot 2>/dev/null || true
zfs create -p $altroot/active/pile-intake
zfs create -p $altroot/active/pile-readonly

export SYSTEM_ROOT=$altroot
file=root-override.txt
mkfile data $file
capture_file $file
system-ingest-pile

assert_file_exists /$altroot/active/pile-readonly/in/$file
assert_not_exists /tank/data/active/pile-readonly/in/$file
