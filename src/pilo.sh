#!/bin/sh
set -eu

HERE=$(dirname $(readlink -f "$0"))

fatal() {
    echo "ERROR: $*" >&2
    exit 1
}

cmd=${1:-}
[ "$cmd" ] || fatal "missing command"
shift

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

: "${PILO_PRIMARY_ROOT:?PILO_PRIMARY_ROOT not set}"
: "${PILO_PATH:?PILO_PATH not set}"
: "${PILO_USER:?PILO_USER not set}"
: "${PILO_ADMIN_PATH:="$PILO_PATH/active/admin"}"
: "${PILO_INTAKE_PATH:="$PILO_PATH/active/pile-intake"}"
: "${PILO_PILE_PATH:="$PILO_PATH/active/pile-readonly"}"
: "${PILO_STATIC_PATH:="$PILO_PATH/static"}"

export PILO_PRIMARY_ROOT
export PILO_SECONDARY_ROOTS
export PILO_USER
export PILO_PATH
export PILO_ADMIN_PATH
export PILO_INTAKE_PATH
export PILO_PILE_PATH
export PILO_STATIC_PATH

export PYTHONPATH=$HERE
export PYTHONDONTWRITEBYTECODE=1

target="$HERE/pilo/cmd/pilo-$cmd.py"
if [ -f "$target" ]
then
        exec python3 "$target" "$@"
else
    fatal "unknown command: $cmd"
fi
