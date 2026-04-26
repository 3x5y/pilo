#!/bin/sh
set -e

echo important > /tank/data/active/admin/file.txt
system-snapshot baseline
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $TEST_REPLICA/active/admin \
                        $TEST_ROOT/active/admin baseline >/dev/null


assert_grep important < /tank/data/active/admin/.zfs/snapshot/baseline/file.txt
