#!/bin/sh
set -e

system-snapshot stale
sleep 2

export CONFIG_SNAPSHOT_MAX_AGE=1
capture_status system-status snapshot

assert_command_fail status returned zero
echo "$OUTPUT" | assert_grep snapshot
