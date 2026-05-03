#!/bin/sh
set -eu

pile="$PILO_PILE_PATH"

if [ "${1:-}" = "--dump" ]
then
    cd "$pile"
    find in -type f | LC_COLLATE=C sort
    exit 0
fi

if [ "${1:-}" = "--script" ]
then
    tmp_before=$(mktemp)
    tmp_after=$(mktemp)

    trap "rm -f $tmp_before $tmp_after" EXIT

    cd "$pile"
    find in -type f | LC_COLLATE=C sort > "$tmp_before"

    cat > "$tmp_after"

    diff -u "$tmp_before" "$tmp_after" || true

    exit 0
fi

echo "ERROR: unsupported mode"
exit 1
