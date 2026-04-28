#!/bin/sh
set -e

snap=t0

system-snapshot $snap
system-replicate

capture_status system-status replication

assert_command_ok replication should be up to date
echo "$OUTPUT" | assert_grep OK.*replication:.$snap
