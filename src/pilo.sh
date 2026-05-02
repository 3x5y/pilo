#!/bin/sh
set -eu

HERE=$(dirname $(readlink -f "$0"))
. "$HERE"/lib.sh

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

: ${PILO_ROOT:=}
: ${PILO_PATH:=}

run_doctor() {
    if ! doctor_output=$(. "$HERE/pilo-doctor.sh" 2>&1)
    then
        echo "$doctor_output" >&2
        exit 1
    fi
}

. "$HERE"/env.sh

require_dir "$PILO_PATH"
require_dataset "$PILO_ROOT"

case "$cmd" in
    doctor|init) ;;
    capture) run_doctor ;;
    *) ;;
esac

target="$HERE/pilo-$cmd.sh"
[ -f "$target" ] || fatal "unknown command: $cmd"
. "$target"
