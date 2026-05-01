#!/bin/sh
set -e

pilo-snapshot stale
sleep 2

export CONFIG_SNAPSHOT_MAX_AGE=1
capture_status pilo-status snapshot

assert_command_fail status returned zero
echo "$OUTPUT" | assert_grep snapshot
