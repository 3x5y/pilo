#!/bin/sh
set -eu

STATUS=0

check_transient() {
    # naive: scan dirs for git repos active and working dir
    dirs="
    $PILO_ADMIN_PATH
    "
    for dir in $(find $dirs -type d -name ".git" 2>/dev/null)
    do
        repo=$(dirname "$dir")
        if ! git -C "$repo" diff --quiet 2>/dev/null
        then
            echo "[WARN] transient: repo $repo has uncommitted changes"
            STATUS=1
        fi
    done
}

check_pile() {
    pile=$PILO_PILE_PATH

    dir_exists "$pile" || return

    now=$(date +%s)
    max_age=${CONFIG_PILE_MAX_AGE:-86400}
    tmp_list=$(tmpfile)
    add_tmpfile_cleanup $tmp_list

    find "$pile" -type f | LC_COLLATE=C sort > "$tmp_list"
    while IFS= read f
    do
        mtime=$(stat -c %Y "$f")
        age=$((now - mtime))

        # 1 day threshold for now (test-friendly)
        if [ "$age" -gt "$max_age" ]
        then
            echo "[WARN] pile: $f is older than threshold"
            STATUS=1
        fi
    done < "$tmp_list"
}

check_snapshot() {
    dataset=$PILO_PILE_DATASET

    snap_info=$(zfs list -t snapshot -o name,creation -s creation \
                | grep "^$dataset@" | tail -n 1)

    snap_name=$(echo "$snap_info" | awk '{print $1}')
    snap_time=$(echo "$snap_info" | cut -d' ' -f2-)

    if [ -z "$snap_name" ]
    then
        echo "[WARN] snapshot: none for $dataset"
        STATUS=1
        return
    fi

    snap_epoch=$(date -d "$snap_time" +%s)
    now=$(date +%s)
    max_age=${CONFIG_SNAPSHOT_MAX_AGE:-3600}
    age=$((now - snap_epoch))

    if [ "$age" -gt "$max_age" ]
    then
        echo "[WARN] snapshot: stale ($age s)"
        STATUS=1
    else
        echo "[OK] snapshot: fresh ($age s)"
    fi
}

check_replication() {
    src="$PILO_ROOT"
    dst="$PILO_REPLICA_ROOT"

    last_src=$(zfs list -t snapshot -o name -s creation | grep "^$src@" | tail -n1)
    last_dst=$(zfs list -t snapshot -o name -s creation | grep "^$dst@" | tail -n1)

    if [ -z "$last_src" ]
    then
        last_src='**MISSING**'
    fi

    src_name=$(echo "$last_src" | cut -d@ -f2)
    dst_name=$(echo "$last_dst" | cut -d@ -f2)

    if [ "$src_name" != "$dst_name" ]
    then
        echo "[WARN] replication: latest=$src_name replicated=$dst_name"
        STATUS=1
    else
        echo "[OK] replication: $src_name"
    fi
}

check_datasets() {
    required="
    $PILO_ADMIN_DATASET
    $PILO_INTAKE_DATASET
    $PILO_PILE_DATASET
    $PILO_COLLECTION_DATASET
    "

    for ds in $required
    do
        if ! dataset_exists "$ds"
        then
            echo "[WARN] incomplete: missing dataset $ds"
            STATUS=1
        fi
    done
}

check="${1:-}"

case "$check" in
    ""|transient) check_transient ;;
esac
case "$check" in
    ""|pile) check_pile ;;
esac
case "$check" in
    ""|snapshot) check_snapshot ;;
esac
case "$check" in
    ""|replication) check_replication ;;
esac
case "$check" in
    ""|datasets) check_datasets ;;
esac

exit $STATUS
