#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-snapshot t1
pilo storage-replica-seed

snap_count=$(zfs list -t snapshot -Ho name | wc -l)

OUT=$(pilo storage-rotate-gc --preview 2>&1)
[ -n "$OUT" ] || fail "expected non-empty preview"
echo "$OUT" | assert_grep "destroy"

[ "$(zfs list -t snapshot -Ho name | wc -l)" -eq "$snap_count" ] \
    || fail "snapshots were destroyed during preview"
