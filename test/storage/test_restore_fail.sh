#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
echo data > /$ADMIN/file.txt
pilo storage-snapshot baseline
# deliberately skip replication
zfs destroy -r $TEST_ROOT

capture_status pilo storage-restore $repl $ADMIN baseline

assert_command_fail recovery succeeded without replica data
