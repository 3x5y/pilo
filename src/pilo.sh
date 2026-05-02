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

require_dir "$PILO_PATH"
require_dataset "$PILO_ROOT"

target="$HERE/pilo-$cmd.sh"

if [ ! -f "$target" ]
then
    echo "ERROR: unknown command: $cmd"
    exit 1
fi

. "$target"
