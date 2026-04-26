#!/bin/sh
set -e

ADMIN=$TEST_ROOT/active/admin
STATIC=$TEST_ROOT/static

echo a0 > /$ADMIN/file.txt
with_dataset_writable $STATIC sh -c "echo s0 > /$STATIC/doc.txt"
system-snapshot t0
system-replicate

echo a1 > /$ADMIN/file.txt
with_dataset_writable $STATIC sh -c "echo s1 > /$STATIC/doc.txt"
system-snapshot t1
system-replicate

assert_grep a1 < /$TEST_REPLICA/active/admin/.zfs/snapshot/t1/file.txt
assert_grep s1 < /$TEST_REPLICA/static/.zfs/snapshot/t1/doc.txt
