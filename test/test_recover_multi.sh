#!/bin/sh
set -e

echo admin-data > /tank/data/active/admin/code.txt
with_dataset_writable tank/data/static \
    sh -c "echo static-data > /tank/data/static/doc.txt"
echo pile-data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
system-snapshot baseline
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $TEST_REPLICA/active/pile-readonly \
                        $TEST_ROOT/active/pile-readonly baseline >/dev/null
system-recover-baseline $TEST_REPLICA/active/admin \
                        $TEST_ROOT/active/admin baseline >/dev/null
system-recover-baseline $TEST_REPLICA/static \
                        $TEST_ROOT/static baseline >/dev/null

assert_grep pile-data < /tank/data/active/pile-readonly/.zfs/snapshot/baseline/in/file.txt
assert_grep admin-data < /tank/data/active/admin/.zfs/snapshot/baseline/code.txt
assert_grep static-data < /tank/data/static/.zfs/snapshot/baseline/doc.txt
