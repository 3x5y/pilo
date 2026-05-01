#!/bin/sh
set -e

repl_pile=$TEST_REPLICA/active/pile-readonly
repl_admin=$TEST_REPLICA/active/admin
repl_static=$TEST_REPLICA/static
admin_file=admin.txt
pile_file=file.txt
static_file=doc.txt

snap=baseline
echo admin-data > /$ADMIN/$admin_file
with_writable $STATIC \
    sh -c "echo static-data > /$STATIC/$static_file"
mkfile pile-data file.txt
capture_file file.txt
pilo-ingest-pile
pilo-snapshot $snap
pilo-replicate
zfs destroy -r $TEST_ROOT

pilo-recover-baseline $repl_static $STATIC $snap >/dev/null
pilo-recover-baseline $repl_pile $PILE $snap >/dev/null
pilo-recover-baseline $repl_admin $ADMIN $snap >/dev/null

assert_grep static-data < /$STATIC/.zfs/snapshot/$snap/$static_file
assert_grep pile-data < /$PILE/.zfs/snapshot/$snap/in/$pile_file
assert_grep admin-data < /$ADMIN/.zfs/snapshot/$snap/$admin_file
