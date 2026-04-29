#!/bin/sh
set -e

system-anchor-create rotation
system-replicate

system-snapshot t1

capture_status system-replicate

assert_command_ok replication failed

# ensure incremental basis was anchor (indirectly)
zfs list -t snap $TEST_REPLICA | assert_grep rotation-
