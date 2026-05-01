#!/bin/sh
set -e

pilo-snapshot-anchor
pilo-replicate

# create multiple snapshots
pilo-snapshot-rpo
pilo-snapshot-anchor

pilo-replicate

# verify latest exists
zfs list -t snapshot | assert_grep "$TEST_REPLICA@a-"
