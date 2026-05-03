#!/bin/sh
set -eu

SRC="$1"
DST_REL="$2"

[ -f "$SRC" ] || {
    echo "ERROR: source file missing: $SRC"
    exit 1
}

case "$DST_REL" in
    in/*)
        DST="$PILO_PILE_PATH/$DST_REL"
        DATASET="$PILO_PILE_DATASET"
        ;;
    collection/*|filing/*)
        DST="$PILO_STATIC_PATH/$DST_REL"
        # dataset resolution later
        ;;
    *)
        echo "ERROR: invalid target path"
        exit 1
        ;;
esac

[ -f "$DST" ] || {
    echo "ERROR: target does not exist: $DST_REL"
    exit 1
}

zfs set readonly=off "$DATASET"
cp "$SRC" "$DST"
chown "$PILO_USER":"$PILO_USER" "$DST"
zfs set readonly=on "$DATASET"

pilo manifest-update
