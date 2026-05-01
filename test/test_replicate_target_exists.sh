#!/bin/sh
set -e

repl=$REPLICA_ROOT/admin

zfs create $repl
zfs snapshot $ADMIN@t0

capture_status pilo-replicate $ADMIN $repl

assert_command_fail
echo "$OUTPUT" | assert_grep 'cannot receive new filesystem stream'
