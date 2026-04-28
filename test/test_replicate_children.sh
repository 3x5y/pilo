#!/bin/sh
set -e

admin=$ACTIVE/admin
repl_admin=$TEST_REPLICA/active/admin
repl_static=$TEST_REPLICA/static
admin_file=admin.txt
static_file=doc.txt

echo a0 > /$admin/$admin_file
with_writable $STATIC \
    sh -c "echo s0 > /$STATIC/doc.txt"
system-snapshot t0
system-replicate

echo a1 > /$admin/$admin_file
with_writable $STATIC \
    sh -c "echo s1 > /$STATIC/doc.txt"
system-snapshot t1
system-replicate

assert_grep a1 < /$repl_admin/.zfs/snapshot/t1/$admin_file
assert_grep s1 < /$repl_static/.zfs/snapshot/t1/$static_file
