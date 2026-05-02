#!/bin/sh
set -eu

src="${1:-"$PILO_ROOT"}"
dst="${2:-"$PILO_REPLICA_ROOT"}"

last_src=$(zfs list -t snapshot -Ho name -s creation "$src" | tail -n1)
last_dst=$(zfs list -t snapshot -Ho name -s creation "$dst" | tail -n1) 2>/dev/null

get_incr_basis() {
    local guid=$(get_latest_guid "$dst")
    zfs list -t snapshot -o name,guid "$src" \
        | awk -v g="$guid" '$2 == g { print $1 }'
}

[ "$last_src" ] || fatal "no source snapshot"

if [ -z "$last_dst" ]
then
    # full send
    zfs send -R "$last_src" \
        | zfs receive -h -u -o readonly=on "$dst"
else
    # incremental
    base=$(get_incr_basis)
    [ "$last_src" != "$base" ] || exit 0
    [ "$base" ] || fatal "base snapshot missing on source: $base"

    zfs send -h -R -I "$base" "$last_src" \
        | zfs receive -u -o readonly=on "$dst"
fi
