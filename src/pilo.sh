#!/bin/sh
set -eu

HERE=$(dirname $(readlink -f "$0"))

cmd=${1:-}
[ -z "$cmd" ] || shift

case "$cmd" in
    "")
        echo "ERROR: missing command"
        exit 1
        ;;
esac

if [ -n "${PILO_CONFIG:-}" ] && [ -r "$PILO_CONFIG" ]
then
    . "$PILO_CONFIG"
elif [ -r /etc/pilo.conf.sh ]
then
    . /etc/pilo.conf.sh
elif [ -r "$HERE"/pilo.conf.sh ]
then
    . "$HERE"/pilo.conf.sh
fi

: ${PILO_ROOT:=}
: ${PILO_PATH:=}

. "$HERE"/env.sh

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
