#!/bin/sh
set -e

pilo snapshot-incr
pilo snapshot-incr

count=$(zfs list -t snapshot -Ho name $TEST_ROOT | grep -- "-incr$" | wc -l)

[ "$count" -eq 2 ] || fail "rpo snapshots not unique"
