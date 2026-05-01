#!/bin/sh
set -eu

NAME="$1"

[ -n "$NAME" ] || {
    echo "usage: pilo-snapshot <name>"
    exit 1
}

zfs snapshot -r "$SYSTEM_ROOT@$NAME"
