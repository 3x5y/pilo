#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

cmd=${1:-}
[ -z "$cmd" ] || shift

case "$cmd" in
    "")
        echo "ERROR: missing command"
        exit 1
        ;;
esac

[ -n "$SYSTEM_ROOT" ] || {
    echo "ERROR: SYSTEM_ROOT not set"
    exit 1
}

[ -n "$SYSTEM_PATH" ] || {
    echo "ERROR: SYSTEM_PATH not set"
    exit 1
}

[ -d "$SYSTEM_PATH" ] || {
    echo "ERROR: path does not exist: $SYSTEM_PATH"
    exit 1
}

if ! zfs list "$SYSTEM_ROOT" >/dev/null 2>&1
then
    echo "ERROR: dataset does not exist: $SYSTEM_ROOT"
    exit 1
fi

target="$HERE/pilo-$cmd.sh"

if [ ! -f "$target" ]
then
    echo "ERROR: unknown command: $cmd"
    exit 1
fi

. "$target"
