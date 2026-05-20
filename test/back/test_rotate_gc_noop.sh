#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

OUT=$(pilo rotate-gc --preview 2>&1)
[ -z "$OUT" ] || fail "expected empty preview, got: $OUT"

capture_status pilo rotate-gc
assert_command_ok
