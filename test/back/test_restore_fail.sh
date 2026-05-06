#!/bin/sh
set -e

repl=$TEST_REPLICA/active/admin
echo data > /$ADMIN/file.txt
pilo snapshot baseline
# deliberately skip replication
zfs destroy -r $TEST_ROOT

capture_status pilo restore $repl $ADMIN baseline

assert_command_fail recovery succeeded without replica data
