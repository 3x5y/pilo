#!/bin/sh
set -eu

mkfile data a.txt
capture_file a.txt
pilo content-ingest

with_writable $COLLECTION \
    touch "$PILO_STATIC_PATH"/collection/b.txt

pilo manifest-update
before=$(runuser git -C "$PILO_ADMIN_PATH/manifest" rev-parse HEAD)

pilo manifest-update
after=$(runuser git -C "$PILO_ADMIN_PATH/manifest" rev-parse HEAD)

[ "$before" = "$after" ] || fail "manifest update not idempotent"
