#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
echo data > /$ADMIN/file.txt
system-snapshot baseline
# deliberately skip replication
zfs destroy -r $TEST_ROOT

capture_status system-recover-baseline $ADMIN $repl baseline >/dev/null

assert_command_fail recovery succeeded without replica data
