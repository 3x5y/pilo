#!/bin/sh
set -e

pilo-snapshot-anchor
pilo-replicate
pilo-replicate

count=$(zfs list -t snapshot | grep "$TEST_REPLICA@" | wc -l)

[ "$count" -eq 1 ] || fail "replication duplicated snapshots"
