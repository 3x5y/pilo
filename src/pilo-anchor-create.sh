#!/bin/sh
set -eu

TYPE="$1"
SRC="$PILO_ROOT"

[ "$TYPE" ] || fatal "missing anchor type"

ts=$(snapshot_timestamp)

case "$TYPE" in
    daily)
        name="daily-$ts"
        hold=0
        ;;
    rotation)
        name="rotation-$ts"
        hold=1
        ;;
    *)
        fatal "invalid anchor type"
        ;;
esac

zfs snapshot -r "$SRC@$name"

if [ "$hold" -eq 1 ]
then
    zfs hold -r repl-anchor "$SRC@$name"
fi
