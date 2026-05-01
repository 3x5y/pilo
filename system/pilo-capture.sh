#!/bin/sh
set -eu

intake_ds=$SYSTEM_ROOT/active/pile-intake

zfs list "$intake_ds" >/dev/null 2>&1 || {
    echo "ERROR: missing required dataset: $intake_ds"
    exit 1
}

cp -a "$1" $SYSTEM_INTAKE_PATH/
