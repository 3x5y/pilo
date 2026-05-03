#!/bin/sh
set -eu

SRC="$1"
DST_REL="$2"

file_exists "$SRC" || fatal "source file missing: $SRC"

dataset_for_path() {
    case "$1" in
        in/*)
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


case "$DST_REL" in
    in/*)
        DST="$PILO_PILE_PATH/$DST_REL"
        DATASET="$PILO_PILE_DATASET"
        ;;
    collection/*|filing/*)
        DST="$PILO_STATIC_PATH/$DST_REL"
        DATASET=$(dataset_for_path "$DST_REL")
        ;;
    *)
        fatal "invalid target path"
        ;;
esac

file_exists "$DST" || fatal "target does not exist: $DST_REL"

zfs set readonly=off "$DATASET"
cp "$SRC" "$DST"
chown "$PILO_USER":"$PILO_USER" "$DST"
zfs set readonly=on "$DATASET"

pilo manifest-update
