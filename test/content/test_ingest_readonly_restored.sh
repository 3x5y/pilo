#!/bin/sh
set -e

file=a.txt
mkfile data $file
capture_file $file
pilo content-ingest
# inject conflict
mkintake bad $file

capture_status pilo content-ingest

# regardless of failure, dataset must be readonly
[ "$(zfs get -H -o value readonly $PILE)" = "on" ] \
    || fail "readonly not restored after failure"
