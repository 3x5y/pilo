#!/bin/sh
set -e

echo important > /tank/data/active/pile/canon.txt
echo temporary > /tank/data/stash/temp.txt

zfs snapshot tank/data/active/pile@canon_test

assert_file_exists /tank/data/active/pile/.zfs/snapshot/canon_test/canon.txt
assert_not_exists /tank/data/active/pile/.zfs/snapshot/canon_test/temp.txt
