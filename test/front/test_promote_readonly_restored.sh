#!/bin/sh
set -eu

with_writable $COLLECTION \
    sh -c "echo A > '$PILO_STATIC_PATH/collection/x.txt'"

with_writable $PILE \
    sh -c "echo B > '$PILO_PILE_PATH/out/collection/x.txt'"

capture_status pilo static-promote

assert_command_fail

[ "$(zfs get -H -o value readonly "$COLLECTION")" = on ] \
    || fail "static dataset left writable"
