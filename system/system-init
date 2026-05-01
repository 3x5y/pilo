#!/bin/sh
set -eu

root=$SYSTEM_ROOT
pile=$SYSTEM_PILE_PATH

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
zfs set readonly=on $root/active/pile-readonly
zfs set readonly=on $root/static/collection
#zfs set readonly=on $root/static/filing/2025
