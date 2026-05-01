#!/bin/sh
set -eu

dataset=$SYSTEM_ROOT/active/pile-readonly
pile=$SYSTEM_PILE_PATH
manifest=$pile/.manifest

zfs list $dataset >/dev/null 2>&1 || {
    echo "ERROR: missing required dataset: $dataset"
    exit 1
}

tmp=$(mktemp)

cd $pile

find . -type f ! -name .manifest -print0 \
  | LC_COLLATE=C sort -z \
  | xargs -r0 sha256sum > "$tmp"

zfs set readonly=off $dataset
mv "$tmp" $manifest
zfs set readonly=on $dataset
