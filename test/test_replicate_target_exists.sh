#!/bin/sh
set -e

repl=$TEST_REPLICA_ROOT/admin

zfs create $repl
zfs snapshot $ADMIN@t0

capture_status system-replicate $ADMIN $repl

assert_command_fail
echo "$OUTPUT" | assert_grep 'cannot receive new filesystem stream'
