#!/bin/sh
set -e

DATA_ROOT=$TEST_ROOT
REPL_ROOT=$TEST_REPLICA

echo admin-data > /tank/data/active/admin/code.txt
echo archive-data > /tank/data/archive/doc.txt
echo pile-data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
zfs snapshot -r $DATA_ROOT@baseline
zfs send -R $DATA_ROOT@baseline | zfs receive -F $REPL_ROOT
zfs destroy -r $DATA_ROOT

system-recover-baseline $REPL_ROOT/active/pile-readonly \
                        $DATA_ROOT/active/pile-readonly baseline >/dev/null
system-recover-baseline $REPL_ROOT/active/admin \
                        $DATA_ROOT/active/admin baseline >/dev/null
system-recover-baseline $REPL_ROOT/archive \
                        $DATA_ROOT/archive baseline >/dev/null

assert_grep pile-data < /tank/data/active/pile-readonly/.zfs/snapshot/baseline/file.txt
assert_grep admin-data < /tank/data/active/admin/.zfs/snapshot/baseline/code.txt
assert_grep archive-data < /tank/data/archive/.zfs/snapshot/baseline/doc.txt
