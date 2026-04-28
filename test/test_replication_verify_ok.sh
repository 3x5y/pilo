#!/bin/sh
set -e

# initial snapshot + replication
system-snapshot t0
system-replicate

# new snapshot
system-snapshot t1
system-replicate

capture_status system-replication-verify

assert_command_ok replication continuity broken
