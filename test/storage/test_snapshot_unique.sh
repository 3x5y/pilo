#!/bin/sh
set -e

pilo storage-snapshot-reg
pilo storage-snapshot-reg

count=$(zfs list -t snapshot -Ho name $TEST_ROOT | grep -- "-reg$" | wc -l)

[ "$count" -eq 2 ] || fail "rpo snapshots not unique"
