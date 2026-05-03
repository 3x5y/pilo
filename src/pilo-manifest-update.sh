#!/bin/sh
set -eu

dataset=$PILO_PILE_DATASET
pile=$PILO_PILE_PATH
manifest=$pile/.manifest

require_dataset "$dataset"

tmp=$(mktemp)
chmod +r $tmp
cd $pile
generate_manifest > "$tmp"
with_writable $dataset \
    mv "$tmp" $manifest

as_user mkdir -p "$PILO_ADMIN_PATH"/manifest
as_user cp $manifest "$PILO_ADMIN_PATH"/manifest/pile.manifest
