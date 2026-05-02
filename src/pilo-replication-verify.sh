#!/bin/sh
set -eu

status_ok() {
    echo "STATUS=OK"
    exit 0
}

status_fail() {
    echo "STATUS=$1"
    shift
    fatal "$@"
}

SRC=${1:-"$PILO_ROOT"}
DST=${2:-"$PILO_REPLICA_ROOT"}

SRC_GUID=$(get_latest_guid "$SRC")
DST_GUID=$(get_latest_guid "$DST")

if [ -z "$DST_GUID" ]
then
    status_fail EMPTY "no snapshots on target"
fi

SRC_GUIDS=$(tmpfile)
DST_GUIDS=$(tmpfile)

map() {
    local name=$1
    local from=$2
    local onto=$3
    local suffix=${name#"$from"}
    suffix=${suffix#/}
    echo "$onto${suffix:+/$suffix}"
}

# iterate datasets on target
zfs list -r -t filesystem -Ho name "$DST" | while read -r dst_ds
do
    src_ds=$(map "$dst_ds" "$DST" "$SRC")
    zfs list -t snap -Ho guid "$src_ds" | sort > "$SRC_GUIDS"
    zfs list -t snap -Ho guid "$dst_ds" | sort > "$DST_GUIDS"

    if comm -23 "$DST_GUIDS" "$SRC_GUIDS" | grep -q .
    then
        status_fail DIVERGED "replication divergence in $dst_ds"
    fi

    src_latest=$(get_latest_guid "$src_ds")
    dst_latest=$(get_latest_guid "$dst_ds")

    if [ -n "$dst_latest" ] && [ "$src_latest" != "$dst_latest" ]
    then
        status_fail BEHIND "replication behind in $dst_ds"
    fi
done

zfs list -r -t filesystem -Ho name "$SRC" | while read -r src_ds
do
    dst_ds=$(map "$src_ds" "$SRC" "$DST")
    if ! zfs list "$dst_ds" >/dev/null 2>&1
    then
        status_fail BEHIND "replication behind, missing $dst_ds"
        exit 1
    fi
done

if [ "$SRC_GUID" != "$DST_GUID" ]
then
    status_fail UNKNOWN GUID mismatch "$SRC != $DST"
    exit 1
fi

status_ok
