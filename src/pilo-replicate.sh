#!/bin/sh
set -eu

src="${1:-"$SYSTEM_ROOT"}"
dst="${2:-"$SYSTEM_REPLICA_ROOT"}"

last_src=$(zfs list -t snapshot -Ho name -s creation "$src" | tail -n1)
last_dst=$(zfs list -t snapshot -Ho name -s creation "$dst" | tail -n1) 2>/dev/null

get_incr_basis() {
    local dst_guid=$(zfs list -t snapshot -Ho guid -s creation "$dst" | tail -n1)

    zfs list -t snapshot -o name,guid "$src" \
        | awk -v g="$dst_guid" '$2 == g { print $1 }'
}

if [ -z "$last_src" ]
then
    echo "ERROR: no source snapshot"
    exit 1
fi

if [ -z "$last_dst" ]
then
    zfs send -R "$last_src" \
        | zfs receive -h -u -o readonly=on "$dst"
else

    base=$(get_incr_basis)

    if [ "$last_src" = "$base" ]
    then
        exit 0
    fi

    [ -n "$base" ] || {
        echo "ERROR: base snapshot missing on source: $base"
        exit 1
    }
    zfs send -h -R -I "$base" "$last_src" \
        | zfs receive -u -o readonly=on "$dst"
fi
