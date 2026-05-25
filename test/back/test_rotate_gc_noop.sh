#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

OUT=$(pilo storage-rotate-gc --preview 2>&1)
[ -z "$OUT" ] || fail "expected empty preview, got: $OUT"

capture_status pilo storage-rotate-gc
assert_command_ok
