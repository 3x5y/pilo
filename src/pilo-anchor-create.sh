#!/bin/sh
set -eu

require_arg "${1:-}" "missing anchor type"

TYPE="$1"
SRC="$PILO_ROOT"

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

snapshot "$name" "$SRC"

if [ "$hold" -eq 1 ]
then
    zfs hold -r repl-anchor "$SRC@$name"
fi
