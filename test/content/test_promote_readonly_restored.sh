#!/bin/sh
set -eu

with_writable $COLLECTION \
    sh -c "echo A > '/$STATIC/collection/x.txt'"

echo B > /$PILE/out/collection/x.txt

capture_status pilo content-promote

assert_command_fail

[ "$(zfs get -H -o value readonly "$COLLECTION")" = on ] \
    || fail "static dataset left writable"
