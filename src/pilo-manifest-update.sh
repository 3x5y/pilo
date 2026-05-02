#!/bin/sh
set -eu

dataset=$PILO_PILE_DATASET
pile=$PILO_PILE_PATH
manifest=$pile/.manifest

require_dataset "$dataset"

tmp=$(mktemp)
cd $pile
generate_manifest > "$tmp"
with_writable $dataset \
    mv "$tmp" $manifest
