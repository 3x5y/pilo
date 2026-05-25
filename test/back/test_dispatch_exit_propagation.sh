#!/bin/sh
set -e

capture_status pilo storage-replication-verify

# may fail depending on state, but must propagate
[ "$STATUS" -ne 127 ] || fail "dispatch failed to execute command"
