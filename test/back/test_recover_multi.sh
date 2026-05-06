#!/bin/sh
set -e

repl_pile=$TEST_REPLICA/active/pile-readonly
repl_admin=$TEST_REPLICA/active/admin
repl_coll=$TEST_REPLICA/static/collection
admin_file=admin.txt
pile_file=file.txt
static_file=doc.txt

snap=baseline
echo admin-data > /$ADMIN/$admin_file
with_writable $COLLECTION \
    sh -c "echo static-data > /$COLLECTION/$static_file"
mkfile pile-data file.txt
capture_file file.txt
pilo ingest-pile
pilo snapshot $snap
pilo replicate
zfs destroy -r $COLLECTION
zfs destroy -r $PILE
zfs destroy -r $ADMIN

pilo recover-baseline $COLLECTION 2>/dev/null
pilo recover-baseline $PILE 2>/dev/null
pilo recover-baseline $ADMIN >/dev/null

assert_grep static-data < /$COLLECTION/.zfs/snapshot/$snap/$static_file
assert_grep pile-data < /$PILE/.zfs/snapshot/$snap/in/$pile_file
assert_grep admin-data < /$ADMIN/.zfs/snapshot/$snap/$admin_file
