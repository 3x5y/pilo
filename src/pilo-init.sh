#!/bin/sh
set -eu

require_dataset() {
    if ! zfs list "$1" >/dev/null 2>&1
    then
        echo "ERROR: missing required dataset: $1"
        exit 1
    fi
}

ensure_dir() {
    [ -d "$1" ] || mkdir -p "$1"
}

set_readonly() {
    zfs set readonly=on "$1"
}

: "${PILO_ADMIN_PATH:=$PILO_PATH/active/admin}"
: "${PILO_INTAKE_PATH:=$PILO_PATH/active/pile-intake}"
: "${PILO_PILE_PATH:=$PILO_PATH/active/pile-readonly}"
: "${PILO_STATIC_PATH:=$PILO_PATH/static}"

root=$PILO_ROOT
pile=$PILO_PILE_PATH

require_dataset $root/active/pile-intake
require_dataset $root/active/pile-readonly
require_dataset $root/active/admin
#require_dataset $root/stash
require_dataset $root/static/collection
#require_dataset $root/static/filing/2025

ensure_dir "$pile/in"
ensure_dir "$pile/sort"
ensure_dir "$pile/out"
ensure_dir "$pile/out/collection"
ensure_dir "$pile/out/filing"

# protected areas
set_readonly $root/active/pile-readonly
set_readonly $root/static/collection
#zfs set readonly=on $root/static/filing/2025
