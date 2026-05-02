#!/bin/sh
set -eu

dataset=$PILO_INTAKE_DATASET

zfs list "$dataset" >/dev/null 2>&1 || {
    echo "ERROR: missing required dataset: $dataset"
    exit 1
}

cp -a "$1" $PILO_INTAKE_PATH/
