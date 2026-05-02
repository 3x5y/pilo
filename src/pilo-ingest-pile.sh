#!/bin/sh
set -eu

intake_dataset=$PILO_INTAKE_DATASET
pile_dataset=$PILO_PILE_DATASET
intake_path=$PILO_INTAKE_PATH
pile_path=$PILO_PILE_PATH

require_dataset $intake_dataset
require_dataset $pile_dataset

tmp_list=$(mktemp)
trap "rm -f '$tmp_list'" EXIT

find "$intake_path" -type f | LC_COLLATE=C sort > "$tmp_list"

while IFS= read -r src
do
    rel=${src#$intake_path/}
    dst="$pile_path/in/$rel"
    dst_dir=$(dirname "$dst")

    if [ -f "$dst" ]
    then
        if cmp -s "$src" "$dst"
        then
            rm "$src" # idempotent
        else
            echo "ERROR: name collision with different content: '$rel'"
            exit 1
        fi
    else
        zfs set readonly=off $pile_dataset
        mkdir -p "$dst_dir"
        mv "$src" "$dst"
        zfs set readonly=on $pile_dataset
    fi
done < "$tmp_list"

pilo manifest-update
