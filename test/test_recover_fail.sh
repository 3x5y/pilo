#!/bin/sh
set -e

admin=$ACTIVE/admin
repl=$TEST_REPLICA/active/admin
echo data > /$admin/file.txt
system-snapshot baseline
# deliberately skip replication
zfs destroy -r $TEST_ROOT

capture_status system-recover-baseline $admin $repl baseline >/dev/null

assert_command_fail recovery succeeded without replica data
