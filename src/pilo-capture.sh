#!/bin/sh
set -eu

intake_ds=$PILO_ROOT/active/pile-intake

zfs list "$intake_ds" >/dev/null 2>&1 || {
    echo "ERROR: missing required dataset: $intake_ds"
    exit 1
}

cp -a "$1" $PILO_INTAKE_PATH/
