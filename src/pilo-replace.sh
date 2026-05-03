#!/bin/sh
set -eu

SRC="$1"
DST_REL="$2"

replace_file() {
    local src=$1
    local dst=$2
    cp "$src" "$dst"
    chown "$PILO_USER":"$PILO_USER" "$dst"
}


case "$DST_REL" in
    in/*|out/*|sort/*)
        DST="$PILO_PILE_PATH/$DST_REL"
        DATASET="$PILO_PILE_DATASET"
        ;;
    collection/*)
        DST="$PILO_STATIC_PATH/$DST_REL"
        DATASET="$PILO_STATIC_DATASET/collection"
        ;;
    filing/*)
        DST="$PILO_STATIC_PATH/$DST_REL"
        sub=$(echo "$DST_REL" | cut -d/ -f2)
        DATASET="$PILO_STATIC_DATASET/filing/$sub"
        ;;
    *)
        fatal "invalid target path"
        ;;
esac

file_exists "$SRC" || fatal "source file missing: $SRC"
file_exists "$DST" || fatal "target does not exist: $DST_REL"

with_writable "$DATASET" \
    replace_file "$SRC" "$DST"

pilo manifest-update
