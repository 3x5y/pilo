#!/bin/sh
set -eu

STATUS=0

warn() {
    error "$@"
    STATUS=1
}

check_dataset() {
    if ! dataset_exists "$1"
    then
        warn "missing required dataset: $1"
    fi
}

check_readonly() {
    if [ "$(get_readonly "$1")" != on ]
    then
        warn "dataset not readonly: $1"
    fi
}

check_dir() {
    if ! dir_exists "$1"
    then
        warn "missing directory: $1"
    fi
}

check_dataset "$PILO_ADMIN_DATASET"
check_dataset "$PILO_INTAKE_DATASET"
check_dataset "$PILO_PILE_DATASET"
check_dataset "$PILO_COLLECTION_DATASET"

check_readonly "$PILO_PILE_DATASET"
check_readonly "$PILO_COLLECTION_DATASET"

check_dir "$PILO_PILE_PATH/in"
check_dir "$PILO_PILE_PATH/out"

exit $STATUS
