#!/bin/sh
set -eu

STATUS=0

error() {
    echo "ERROR: $*" >&2
    STATUS=1
}

check_dataset() {
    if ! dataset_exists "$1"
    then
        error "missing required dataset: $1"
    fi
}

check_readonly() {
    val=$(zfs get -H -o value readonly "$1")
    if [ "$val" != "on" ]
    then
        error "dataset not readonly: $1"
    fi
}

check_dataset "$PILO_ADMIN_DATASET"
check_dataset "$PILO_INTAKE_DATASET"
check_dataset "$PILO_PILE_DATASET"
check_dataset "$PILO_COLLECTION_DATASET"

check_readonly "$PILO_PILE_DATASET"
check_readonly "$PILO_COLLECTION_DATASET"

exit $STATUS
