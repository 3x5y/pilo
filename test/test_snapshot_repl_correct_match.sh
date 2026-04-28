#!/bin/sh
set -e

system-snapshot-anchor
system-replicate

# create multiple snapshots
system-snapshot-rpo
system-snapshot-anchor

system-replicate

# verify latest exists
zfs list -t snapshot | assert_grep "$TEST_REPLICA@a-"
