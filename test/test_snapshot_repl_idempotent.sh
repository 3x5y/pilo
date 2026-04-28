#!/bin/sh
set -e

system-snapshot-anchor
system-replicate
system-replicate

count=$(zfs list -t snapshot | grep "$TEST_REPLICA@" | wc -l)

[ "$count" -eq 1 ] || fail "replication duplicated snapshots"
