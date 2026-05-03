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


validate_file() {
    src="$1"
    target="$2"
    rel="$3"

    dataset="$static_dataset/$target"
    dst="$static_path/$target/$rel"

    require_dataset "$dataset"
    if [ -f "$dst" ] && ! cmp -s "$src" "$dst"
    then
        fatal "destination conflict for $rel"
    fi
}

apply_file() {
    src="$1"
    target="$2"
    rel="$3"

    dataset="$static_dataset/$target"
    dst="$static_path/$target/$rel"
    dst_dir=$(dirname "$dst")

    if [ ! -f "$dst" ]
    then
        with_writable "$dataset" \
            as_user mkdir -p "$dst_dir"
        with_writable "$dataset" \
            cp -a "$src" "$dst"
    fi

    with_writable "$pile_dataset" \
        rm "$src"
}

# collection
col_tmp=$(tmpfile)
fil_tmp=$(tmpfile)
add_tmpfile_cleanup $col_tmp $fil_tmp
find "$out_path/collection" -type f > "$col_tmp"
find "$out_path/filing" -type f > "$fil_tmp"


# validate paths first

while IFS= read -r f
do
    rel=${f#$out_path/collection/}
    validate_file "$f" collection "$rel"
done < "$col_tmp"

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
    validate_file "$f" "filing/$dataset" "$subpath"
done < "$fil_tmp"


# then apply changes

while IFS= read -r f
do
    rel=${f#$out_path/collection/}
    apply_file "$f" collection "$rel"
done < "$col_tmp"

while IFS= read -r f
do
    rel=${f#$out_path/filing/}
    dataset=${rel%%/*}
    subpath=${rel#*/}
    apply_file "$f" "filing/$dataset" "$subpath"
done < "$fil_tmp"

# update manifests
pilo manifest-update
