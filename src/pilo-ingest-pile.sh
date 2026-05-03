#!/bin/sh
set -eu

intake_dataset=$PILO_INTAKE_DATASET
pile_dataset=$PILO_PILE_DATASET
intake_path=$PILO_INTAKE_PATH
pile_path=$PILO_PILE_PATH

require_dataset $intake_dataset
require_dataset $pile_dataset

tmp_list=$(tmpfile)
add_tmpfile_cleanup $tmp_list

find "$intake_path" -type f | LC_COLLATE=C sort > "$tmp_list"

while IFS= read -r src
do
    rel=${src#$intake_path/}
    dst="$pile_path/in/$rel"

    if [ -f "$dst" ] && ! cmp -s "$src" "$dst"
    then
        fatal "name collision with different content: '$rel'"
    fi
done < "$tmp_list"

apply_changes() {
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
                fatal "name collision with different content: '$rel'"
            fi
        else
            ensure_dir "$dst_dir"
            mv "$src" "$dst"
            chown $PILO_USER:$PILO_USER "$dst"
        fi
    done < "$tmp_list"
}

with_writable $pile_dataset \
    apply_changes

pilo manifest-update
