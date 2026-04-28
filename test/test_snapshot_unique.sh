#!/bin/sh
set -e

system-snapshot-anchor
system-snapshot-anchor

count=$(zfs list -t snapshot $TEST_ROOT | grep "@a-" | wc -l)

[ "$count" -eq 2 ] || fail "anchor snapshots not unique"
