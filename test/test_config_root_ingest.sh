#!/bin/sh
set -e

altroot=tank/test-alt

zfs destroy -r $altroot 2>/dev/null || true
zfs create $altroot
OLDPILE=$PILE
init_system $altroot /$altroot
file=root-override.txt
mkfile data $file
capture_file $file
system-ingest-pile

assert_file_exists /$PILE/in/$file
assert_not_exists /$OLDPILE/in/$file
