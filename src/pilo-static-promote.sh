#!/bin/sh
set -eu

pile_dataset=$PILO_PILE_DATASET
static_dataset=$PILO_STATIC_DATASET
static_path=$PILO_STATIC_PATH
out_path="$PILO_PILE_PATH/out"

[ -d "$out_path" ] || mkdir -p "$out_path"

# validate allowed top-level dirs
for d in "$out_path"/*
do
    [ -e "$d" ] || continue
    name=$(basename "$d")

    case "$name" in
        collection|filing) ;;
        *)
            echo "ERROR: invalid /out/ structure: $name"
            exit 1
            ;;
    esac
done

if [ -z "$(find "$out_path" -type f -print -quit)" ]
then
    echo "ERROR: /out/ directory empty"
    exit 1
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
            echo "ERROR: destination conflict for $relpath"
            exit 1
        fi
    else
        with_writable $dataset \
            mkdir -p "$dst_dir"
        with_writable $dataset \
            cp "$src" "$dst"
    fi

    with_writable $pile_dataset \
        rm "$src"
}

COL_TMP=$(mktemp)
FIL_TMP=$(mktemp)
trap "rm -f '$COL_TMP' '$FIL_TMP'" EXIT

# collection
find "$out_path/collection" -type f > "$COL_TMP"
while IFS= read -r f
do
    rel=${f#$out_path/collection/}
    process_file "$f" collection "$rel"
done < "$COL_TMP"

# filing
find "$out_path/filing" -type f > "$FIL_TMP"
while IFS= read -r f
do
    rel=${f#$out_path/filing/}
    case "$rel" in
        */*)
            dataset=${rel%%/*}
            subpath=${rel#*/}
            ;;
        *)
            echo "ERROR: invalid filing structure"
            exit 1
            ;;
    esac
    process_file "$f" "filing/$dataset" "$subpath"
done < "$FIL_TMP"

# update manifests
pilo manifest-update
(
    cd "$static_path"
    tmp=$(mktemp)
    find . -type f ! -name .manifest -print0 \
      | LC_COLLATE=C sort -z \
      | xargs -r0 sha256sum > "$tmp"
    with_writable $static_dataset \
        mv "$tmp" .manifest
)

