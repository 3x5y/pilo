#!/bin/sh
set -eu

pile="$PILO_PILE_PATH"

if [ "${1:-}" = "--dump" ]
then
    cd "$pile"
    find in -type f | LC_COLLATE=C sort
    exit 0
fi

echo "ERROR: unsupported mode"
exit 1
