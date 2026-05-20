#!/bin/sh
set -e

pilo snapshot-rpo
pilo snapshot-rpo

count=$(zfs list -t snapshot $TEST_ROOT | grep "@r-" | wc -l)

[ "$count" -eq 2 ] || fail "rpo snapshots not unique"
