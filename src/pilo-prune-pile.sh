#!/bin/sh
set -eu

dataset=$PILO_ROOT/active/pile-readonly
path=$PILO_PILE_PATH

with_writable() {
    dataset=$1
    shift
    zfs set readonly=off $dataset
    set +e
    "$@"
    result=$?
    set -e
    zfs set readonly=on $dataset
    [ $result -eq 0 ] || exit $result
}

with_writable $dataset \
    find "$path" -mindepth 2 -type d -empty -delete
