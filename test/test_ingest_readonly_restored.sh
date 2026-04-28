#!/bin/sh
set -e

file=a.txt
mkfile data $file
capture_file $file
system-ingest-pile
# inject conflict
mkintake bad $file

capture_status system-ingest-pile

# regardless of failure, dataset must be readonly
[ "$(zfs get -H -o value readonly $PILE)" = "on" ] \
    || fail "readonly not restored after failure"
