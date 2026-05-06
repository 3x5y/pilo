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

: "${PILO_USER:?PILO_USER not set}"
: "${PILO_ROOT:?PILO_ROOT not set}"
: "${PILO_PATH:?PILO_PATH not set}"
#: "${PILO_REPLICA_ROOT:?PILO_REPLICA_ROOT not set}"
: "${PILO_ACTIVE_DATASET:="$PILO_ROOT/active"}"
: "${PILO_ADMIN_DATASET:="$PILO_ROOT/active/admin"}"
: "${PILO_INTAKE_DATASET:="$PILO_ROOT/active/pile-intake"}"
: "${PILO_PILE_DATASET:="$PILO_ROOT/active/pile-readonly"}"
: "${PILO_STASH_DATASET:="$PILO_ROOT/stash"}"
: "${PILO_STATIC_DATASET:="$PILO_ROOT/static"}"
: "${PILO_COLLECTION_DATASET:="$PILO_ROOT/static/collection"}"
: "${PILO_FILING_DATASET:="$PILO_ROOT/static/filing"}"
: "${PILO_ADMIN_PATH:="$PILO_PATH/active/admin"}"
: "${PILO_INTAKE_PATH:="$PILO_PATH/active/pile-intake"}"
: "${PILO_PILE_PATH:="$PILO_PATH/active/pile-readonly"}"
: "${PILO_STATIC_PATH:="$PILO_PATH/static"}"

export PILO_ROOT
export PILO_PATH
export PILO_USER
export PILO_REPLICA_ROOT
export PILO_ACTIVE_DATASET
export PILO_ADMIN_DATASET
export PILO_INTAKE_DATASET
export PILO_PILE_DATASET
export PILO_STASH_DATASET
export PILO_STATIC_DATASET
export PILO_COLLECTION_DATASET
export PILO_FILING_DATASET
export PILO_ADMIN_PATH
export PILO_INTAKE_PATH
export PILO_PILE_PATH
export PILO_STATIC_PATH

case "$cmd" in
    recover|restore*) ;;
    *)
        require_dir "$PILO_PATH"
        require_dataset "$PILO_ROOT"
        ;;
esac

target="$HERE/pilo-$cmd"
if [ -f "$target".py ]
then
    exec python3 "$target".py "$@"
elif [ -f "$target".sh ]
then
    . "$target".sh
else
    fatal "unknown command: $cmd"
fi
