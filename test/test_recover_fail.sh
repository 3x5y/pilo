#!/bin/sh
set -e

echo data > /tank/data/active/admin/file.txt
system-snapshot baseline
# deliberately skip replication
zfs destroy -r $TEST_ROOT

capture_status system-recover-baseline \
    $TEST_REPLICA/active/admin \
    $TEST_ROOT/active/admin baseline >/dev/null

assert_command_fail recovery succeeded without replica data
