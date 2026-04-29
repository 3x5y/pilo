#!/bin/sh
set -e

admin=$ACTIVE/admin
repl=$TEST_REPLICA_ROOT/admin

zfs create $repl
zfs snapshot $admin@t0

capture_status system-replicate $admin $repl
#system-replicate $admin $repl

assert_command_fail
echo "$OUTPUT" | assert_grep 'cannot receive new filesystem stream'
