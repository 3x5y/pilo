#!/bin/sh
set -eu

dataset=$PILO_PILE_DATASET
pile=$PILO_PILE_PATH
manifest=$pile/.manifest

require_dataset "$dataset"

tmp=$(mktemp)

cd $pile

find . -type f ! -name .manifest -print0 \
  | LC_COLLATE=C sort -z \
  | xargs -r0 sha256sum > "$tmp"

with_writable $dataset \
    mv "$tmp" $manifest
