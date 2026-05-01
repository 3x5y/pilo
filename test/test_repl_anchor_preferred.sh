#!/bin/sh
set -e

pilo-anchor-create rotation
pilo-replicate

pilo-snapshot t1

capture_status pilo-replicate

assert_command_ok replication failed

# ensure incremental basis was anchor (indirectly)
zfs list -t snap $TEST_REPLICA | assert_grep rotation-
