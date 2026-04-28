#!/bin/sh
set -e

admin=$ACTIVE/admin
repl_pile=$TEST_REPLICA/active/pile-readonly
repl_admin=$TEST_REPLICA/active/admin
repl_static=$TEST_REPLICA/static
admin_file=admin.txt
pile_file=file.txt
static_file=doc.txt

snap=baseline
echo admin-data > /$admin/$admin_file
with_writable $STATIC \
    sh -c "echo static-data > /$STATIC/$static_file"
mkfile pile-data file.txt
capture_file file.txt
system-ingest-pile
system-snapshot $snap
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $repl_static $STATIC $snap >/dev/null
system-recover-baseline $repl_pile $PILE $snap >/dev/null
system-recover-baseline $repl_admin $admin $snap >/dev/null

assert_grep static-data < /$STATIC/.zfs/snapshot/$snap/$static_file
assert_grep pile-data < /$PILE/.zfs/snapshot/$snap/in/$pile_file
assert_grep admin-data < /$admin/.zfs/snapshot/$snap/$admin_file
