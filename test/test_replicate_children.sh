#!/bin/sh
set -e

repl_static=$TEST_REPLICA/static

echo a0 > /$ADMIN/admin.txt
with_writable $STATIC \
    sh -c "echo s0 > /$STATIC/doc.txt"
system-snapshot t0
system-replicate

echo a1 > /$ADMIN/admin.txt
with_writable $STATIC \
    sh -c "echo s1 > /$STATIC/doc.txt"
system-snapshot t1
system-replicate

zfs inherit mountpoint $REPLICA_ROOT
assert_grep a1 < /$TEST_REPLICA/active/admin/.zfs/snapshot/t1/admin.txt
assert_grep s1 < /$TEST_REPLICA/static/.zfs/snapshot/t1/doc.txt
