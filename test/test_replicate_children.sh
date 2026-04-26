#!/bin/sh
set -e

ROOT=$TEST_ROOT
DST=$TEST_REPLICA

echo v1 > /tank/data/active/pile-readonly/file.txt
echo a1 > /tank/data/archive/doc.txt

system-snapshot t0
system-replicate $ROOT $DST

echo v2 >> /tank/data/active/pile-readonly/file.txt
echo a2 >> /tank/data/archive/doc.txt

system-snapshot t1

system-replicate $ROOT $DST

assert_grep v2 < /$DST/active/pile-readonly/.zfs/snapshot/t1/file.txt
assert_grep a2 < /$DST/archive/.zfs/snapshot/t1/doc.txt
