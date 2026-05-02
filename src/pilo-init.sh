#!/bin/sh
set -eu

ensure_dir() {
    [ -d "$1" ] || mkdir -p "$1"
}

set_readonly() {
    zfs set readonly=on "$1"
}

require_dataset $PILO_INTAKE_DATASET
require_dataset $PILO_PILE_DATASET
require_dataset $PILO_ADMIN_DATASET
#require_dataset $root/stash
require_dataset $PILO_COLLECTION_DATASET
#require_dataset $root/static/filing/2025

pile=$PILO_PILE_PATH
ensure_dir "$pile/in"
ensure_dir "$pile/sort"
ensure_dir "$pile/out"
ensure_dir "$pile/out/collection"
ensure_dir "$pile/out/filing"

# protected areas
set_readonly $PILO_PILE_DATASET
set_readonly $PILO_COLLECTION_DATASET
#zfs set readonly=on $root/static/filing/2025
