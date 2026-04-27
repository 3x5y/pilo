#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

echo data > /tmp/a.txt
system-capture /tmp/a.txt
system-ingest-pile

# inject conflict
echo bad > /tank/data/active/pile-intake/a.txt

capture_status system-ingest-pile

# regardless of failure, dataset must be readonly
[ "$(zfs get -H -o value readonly $PILE)" = "on" ] \
    || fail "readonly not restored after failure"
