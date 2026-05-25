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
pilo content-ingest
pilo storage-snapshot $snap
pilo storage-replica-seed
clear_holds $COLLECTION
clear_holds $PILE
clear_holds $ADMIN
zfs destroy -r $COLLECTION
zfs destroy -r $PILE
zfs destroy -r $ADMIN

pilo storage-restore $repl_coll $COLLECTION $snap
pilo storage-restore $repl_pile $PILE $snap
pilo storage-restore $repl_admin $ADMIN $snap

assert_grep static-data < /$COLLECTION/.zfs/snapshot/$snap/$static_file
assert_grep pile-data < /$PILE/.zfs/snapshot/$snap/in/$pile_file
assert_grep admin-data < /$ADMIN/.zfs/snapshot/$snap/$admin_file
