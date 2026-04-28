#!/bin/sh
set -e

system-snapshot fresh

export CONFIG_SNAPSHOT_MAX_AGE=60 # redundant but explicit
capture_status system-status snapshot

assert_command_ok status returned nonzero
echo "$OUTPUT" | assert_grep snapshot
