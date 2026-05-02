#!/bin/sh
set -eu

dataset=$PILO_PILE_DATASET
path=$PILO_PILE_PATH

CMD="$1"
TAB='	'


[ -n "$CMD" ] || {
    echo "ERROR: missing command"
    exit 1
}


exec_op() {
    mode="$1"   # validate | apply
    op="$2"
    src="$3"
    dst="$4"

    case "$op" in
        mv) ;;
        *)
            echo "ERROR: unsupported operation: '$op'"
            exit 1
            ;;
    esac

    case "$src" in
        /*|*..*)
            echo "ERROR: invalid source path"
            exit 1
            ;;
    esac

    case "$dst" in
        /*|*..*)
            echo "ERROR: invalid destination path"
            exit 1
            ;;
    esac

    SRC="$path/$src"
    DST="$path/$dst"

    [ -f "$SRC" ] || {
        echo "ERROR: source missing: $src"
        exit 1
    }

    if [ "$mode" = "validate" ]
    then
        if [ -f "$DST" ] && ! cmp -s "$SRC" "$DST"
        then
            echo "ERROR: destination conflict: $dst"
            exit 1
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
        [ -z "$extra" ] || {
            echo "ERROR: invalid command (too many fields)"
            exit 1
        }
        [ -n "$src" ] && [ -n "$dst" ] || {
            echo "ERROR: invalid command: $op '$src' '$dst'"
            exit 1
        }
        if grep -Fxq "$src" "$src_seen"
        then
            echo "ERROR: duplicate source in script: $src"
            exit 1
        fi
        if grep -Fxq "$dst" "$dst_seen"
        then
            echo "ERROR: destination conflict in script: $dst"
            exit 1
        fi

        echo "$dst" >> "$dst_seen"
        echo "$src" >> "$src_seen"
        exec_op validate "$op" "$src" "$dst"
    done < $op_list
}

op_list=$(mktemp)
printf "%s\n" "$CMD" > "$op_list"

src_seen=$(mktemp)
dst_seen=$(mktemp)
validate_ops
rm -f "$src_seen" "$dst_seen"

with_writable $dataset \
    apply_ops

rm -f "$op_list"

pilo manifest-update
