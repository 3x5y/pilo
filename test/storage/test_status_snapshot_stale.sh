#!/bin/sh
set -e

pilo storage-snapshot stale
pilo storage-replica-seed
sleep 2

export PILO_SNAPSHOT_MAX_AGE=1
capture_status pilo status snapshot

assert_command_ok status returned nonzero
echo "$OUTPUT" | assert_grep snapshot.stale
