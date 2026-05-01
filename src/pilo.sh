#!/bin/sh
set -eu

HERE=$(readlink -f "$(dirname -- "$0")")

cmd=${1:-}
[ -z "$cmd" ] || shift

case "$cmd" in
    "")
        echo "ERROR: missing command"
        exit 1
        ;;
esac

if [ -n "${PILO_CONFIG:-}" ] && [ -f "$PILO_CONFIG" ]
then
    . "$PILO_CONFIG"
    return
fi

[ -n "$PILO_ROOT" ] || {
    echo "ERROR: PILO_ROOT not set"
    exit 1
}

[ -n "$PILO_PATH" ] || {
    echo "ERROR: PILO_PATH not set"
    exit 1
}

[ -d "$PILO_PATH" ] || {
    echo "ERROR: path does not exist: $PILO_PATH"
    exit 1
}

if ! zfs list "$PILO_ROOT" >/dev/null 2>&1
then
    echo "ERROR: dataset does not exist: $PILO_ROOT"
    exit 1
fi

target="$HERE/pilo-$cmd.sh"

if [ ! -f "$target" ]
then
    echo "ERROR: unknown command: $cmd"
    exit 1
fi

. "$target"
