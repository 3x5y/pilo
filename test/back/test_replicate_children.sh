#!/bin/sh
set -e

repl_static=$TEST_REPLICA/static

echo a0 > /$ADMIN/admin.txt
with_writable $STATIC \
    sh -c "echo s0 > /$STATIC/doc.txt"
pilo snapshot t0
pilo replicate

echo a1 > /$ADMIN/admin.txt
with_writable $COLLECTION \
    sh -c "echo s1 > /$COLLECTION/doc.txt"
pilo snapshot t1
pilo replicate

zfs set canmount=on $TEST_REPLICA/active/admin
zfs set canmount=on $TEST_REPLICA/static/collection
zfs inherit mountpoint $REPLICA_ROOT
zfs inherit mountpoint $TEST_REPLICA
assert_grep a1 < /$TEST_REPLICA/active/admin/.zfs/snapshot/t1/admin.txt
assert_grep s1 < /$TEST_REPLICA/static/collection/.zfs/snapshot/t1/doc.txt
