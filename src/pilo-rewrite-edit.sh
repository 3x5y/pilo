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

    paste "$tmp_before" "$tmp_after" | while read old new
    do
        if [ "$old" != "$new" ]
        then
            printf "mv\t%s\t%s\n" "$old" "$new"
        fi
    done

    exit 0
fi

echo "ERROR: unsupported mode"
exit 1
