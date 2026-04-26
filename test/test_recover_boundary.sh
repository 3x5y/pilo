#!/bin/sh
set -e

echo admin > /tank/data/active/admin/file.txt
echo temp > /tank/data/stash/temp.txt
system-snapshot baseline
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $TEST_REPLICA/active/admin \
                        $TEST_ROOT/active/admin baseline >/dev/null

assert_grep admin < /tank/data/active/admin/.zfs/snapshot/baseline/file.txt
assert_not_exists /tank/data/stash/temp.txt
