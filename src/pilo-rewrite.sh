#!/bin/sh
set -eu

require_arg "${1:-}" "missing command"

CMD="$1"
TAB='	'


domain() {
    case "$1" in
        in/*|out/*|sort/*) echo pile ;;
        collection/*|filing/*) echo static ;;
        *) echo invalid ;;
    esac
}

resolve_path() {
    case "$1" in
        in/*|out/*|sort/*)
            echo "$PILO_PILE_PATH/$1"
            ;;
        collection/*|filing/*)
            echo "$PILO_STATIC_PATH/$1"
            ;;
        *)
            fatal "invalid path root: $1"
            ;;
    esac
}

dataset_for_path() {
    case "$1" in
        in/*|out/*|sort/*)
            echo "$PILO_PILE_DATASET"
            ;;
        collection/*)
            echo "$PILO_STATIC_DATASET/collection"
            ;;
        filing/*)
            sub=$(echo "$1" | cut -d/ -f2)
            echo "$PILO_STATIC_DATASET/filing/$sub"
            ;;
    esac
}

exec_op() {
    mode="$1" # validate | apply
    op="$2"
    src="$3"
    dst="$4"

    case "$op" in
        mv) ;; # valid
        *)
            fatal "unsupported operation: '$op'"
            ;;
    esac

    case "$src" in
        /*|*..*)
            fatal "invalid source path"
            ;;
    esac

    case "$dst" in
        /*|*..*)
            fatal "invalid destination path"
            ;;
    esac

    if [ "$(domain "$src")" != "$(domain "$dst")" ]
    then
        fatal "cross-domain move not allowed"
    fi

    SRC=$(resolve_path "$src")
    DST=$(resolve_path "$dst")

    [ -f "$SRC" ] || fatal "source missing: $src"

    if [ "$mode" = "validate" ]
    then
        if [ -f "$DST" ] && ! cmp -s "$SRC" "$DST"
        then
            fatal "destination conflict: $dst"
        fi
        return
    fi

    ds=$(dataset_for_path "$src")
    with_writable $ds \
        write_change "$SRC" "$DST"
}

write_change() {
    local src=$1
    local dst=$2
    if [ -f "$dst" ]
    then
        rm "$src"
    else
        local dir=$(dirname "$dst")
        mkdir -p "$dir"
        mv "$src" "$dst"
    fi
}

apply_ops() {
    while IFS="$TAB" read -r op src dst extra
    do
        [ -n "$op" ] || continue
        exec_op apply "$op" "$src" "$dst"
    done < $op_list
}

validate_ops() {
    while IFS="$TAB" read -r op src dst extra
    do
        [ -n "$op" ] || continue
        [ -z "$extra" ] || fatal "invalid command (too many fields)"
        if [ -z "$src" ] || [ -z "$dst" ]
        then
            fatal "invalid command: $op '$src' '$dst'"
        fi
        if grep -Fxq "$src" "$src_seen"
        then
            fatal "duplicate source in script: $src"
        fi
        if grep -Fxq "$dst" "$dst_seen"
        then
            fatal "destination conflict in script: $dst"
        fi

        echo "$dst" >> "$dst_seen"
        echo "$src" >> "$src_seen"
        exec_op validate "$op" "$src" "$dst"
    done < $op_list
}

op_list=$(tmpfile)
src_seen=$(tmpfile)
dst_seen=$(tmpfile)
add_tmpfile_cleanup $op_list $src_seen $dst_seen

printf "%s\n" "$CMD" > "$op_list"
validate_ops
apply_ops
pilo manifest-update
# update static manifest too
(
    cd "$PILO_STATIC_PATH"
    tmp=$(mktemp)
    find . -type f ! -name .manifest -print0 \
      | LC_COLLATE=C sort -z \
      | xargs -r0 sha256sum > "$tmp"
    with_writable "$PILO_STATIC_DATASET" \
        mv "$tmp" .manifest
)
