#!/bin/sh
set -eu

pile_dataset=$PILO_PILE_DATASET
static_dataset=$PILO_STATIC_DATASET
static_path=$PILO_STATIC_PATH
out_path="$PILO_PILE_PATH/out"

dir_exists "$out_path" || exit 0

# validate allowed top-level dirs
for d in "$out_path"/*
do
    [ -e "$d" ] || continue
    name=$(basename "$d")

    case "$name" in
        collection|filing) ;;
        *) fatal "invalid /out/ structure: $name" ;;
    esac
done

if [ -z "$(find "$out_path" -type f -print -quit)" ]
then
    fatal "/out/ directory empty"
fi


process_file() {
    local src="$1"
    local target="$2"
    local relpath="$3"
    local dataset="$static_dataset/$target"
    local dst="$static_path/$target/$relpath"
    local dst_dir=$(dirname "$dst")

    require_dataset "$dataset"

    if [ -f "$dst" ]
    then
        if ! cmp -s "$src" "$dst"
        then
            fatal "destination conflict for $relpath"
        fi
        # else idempotent; remove file below
    else
        with_writable $dataset \
            mkdir -p "$dst_dir"
        with_writable $dataset \
            cp "$src" "$dst"
    fi

    with_writable $pile_dataset \
        rm "$src"
}

# collection
col_tmp=$(tmpfile)
find "$out_path/collection" -type f > "$col_tmp"
while IFS= read -r f
do
    rel=${f#$out_path/collection/}
    process_file "$f" collection "$rel"
done < "$col_tmp"

# filing
fil_tmp=$(tmpfile)
find "$out_path/filing" -type f > "$fil_tmp"
while IFS= read -r f
do
    rel=${f#$out_path/filing/}
    case "$rel" in
        */*)
            dataset=${rel%%/*}
            subpath=${rel#*/}
            ;;
        *)
            fatal "invalid filing structure"
            ;;
    esac
    process_file "$f" "filing/$dataset" "$subpath"
done < "$fil_tmp"

# update manifests
pilo manifest-update
tmp=$(mktemp)
cd "$static_path"
generate_manifest > "$tmp"
with_writable $static_dataset \
    mv "$tmp" .manifest
