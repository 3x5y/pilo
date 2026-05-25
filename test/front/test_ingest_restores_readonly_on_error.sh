#!/bin/sh
set -eu

mkintake "A" file.txt
pilo content-ingest
# create conflicting file to trigger failure
mkintake "B" file.txt

capture_status pilo content-ingest

assert_command_fail
[ "$(zfs get -H -o value readonly "$PILE")" = on ] \
    || fail "pile dataset left writable after failure"
