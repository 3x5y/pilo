#!/bin/sh
set -eu

dataset=$PILO_PILE_DATASET
path=$PILO_PILE_PATH

require_arg "${1:-}" "missing command"

CMD="$1"
TAB='	'


exec_op() {
    mode="$1"   # validate | apply
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

    SRC="$path/$src"
    DST="$path/$dst"

    [ -f "$SRC" ] || fatal "source missing: $src"

    if [ "$mode" = "validate" ]
    then
        if [ -f "$DST" ] && ! cmp -s "$SRC" "$DST"
        then
            fatal "destination conflict: $dst"
        fi
        return
    fi

    DIR=$(dirname "$DST")

    if [ -f "$DST" ]
    then
        rm "$SRC"
    else
        mkdir -p "$DIR"
        mv "$SRC" "$DST"
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
printf "%s\n" "$CMD" > "$op_list"
validate_ops
with_writable $dataset \
    apply_ops
pilo manifest-update
