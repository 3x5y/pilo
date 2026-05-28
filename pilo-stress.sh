#!/usr/bin/env bash

set -euo pipefail

SNAPCOLS=name,used,refer,userrefs,creation
INST=$(dirname $0)/pilo-inst
PRI_DEV=/tmp/z0
PRI_POOL=z0-att
PRI_FS=z0-att/pri
SEC_DEV1=/tmp/z1
SEC_DEV2=/tmp/z2
SEC_DEV3=/tmp/z3
SEC_POOL1=z1-rem
SEC_POOL2=z2-rem
SEC_POOL3=z3-rem

#EXPORT_ROOT=/tmp/streams
EXPORT_ROOT=$(mktemp -d)
mkdir $EXPORT_ROOT/local
chown u:u $EXPORT_ROOT $EXPORT_ROOT/local
export PILO_STREAM_OUTPUT_PATH=$EXPORT_ROOT/local


_pilo() {
    echo \# pilo "$@"
    pilo "$@"
}


destroy_pool() {
    local name=$1
    local file=$2
    zpool destroy -f $name || true
    rm -fv $file || true
}


init_pool() {
    local name=$1
    local file=$2
    truncate -s 1G "$file"
    echo \# zpool create -m none -O canmount=off $name "$file"
    zpool create -m none -O canmount=off $name "$file"
}


report_gc() {
    report_target_snapshots
    report_target_holds
    report_source_snapshots
    report_source_holds
}


get_snapshots_to_prune() {
    local fs=$1
    zfs list -t snap -Ho name,userrefs -s createtxg $fs \
        | select_oldest_unref
}


# select only the first (oldest) contiguous set of snapshots without any
# references (holds or clones)

select_oldest_unref() {
    local name refs
    while read name refs
    do
        [ "$refs" -eq 0 ] || break
        echo $name
    done
}


get_target_holds_to_release() {
    zfs list -t snap -s createtxg -Ho name,guid,userrefs $TARGET_FS \
        | select_held_without_source
}


select_held_without_source() {
    while read name guid refs
    do
        if zfs list -t snap -Ho guid $PRI_FS | grep -q ^$guid$
        then
            break
        fi
        [ "$refs" -gt 0 ] || continue
        zfs holds -Hp $name | cut -f1 | sort -u
    done
}


get_source_holds_to_release() {
    local keep=1
    zfs list -t snap -Ho name -s createtxg $PRI_FS \
        | xargs -r zfs holds -Hp \
        | grep "\s$HOLD_TAG\s" \
        | head -n-$keep \
        | cut -f1
}


report_target_snapshots() {
    echo == target snapshots
    zfs list -t snap -o $SNAPCOLS $TARGET_FS
    echo

    echo == target snapshots to prune
    get_snapshots_to_prune $TARGET_FS \
        | xargs -r zfs list -o $SNAPCOLS
    echo
}


report_target_holds() {
    echo == target holds
    zfs list -t snap -Ho name -s createtxg $TARGET_FS \
        | xargs -r zfs holds
    echo

    echo == target holds to release
    get_target_holds_to_release | xargs -r zfs holds
    echo
}


report_source_snapshots() {
    echo == source snapshots
    zfs list -t snap -o $SNAPCOLS $PRI_FS
    echo

    echo == source snapshots to prune
    get_snapshots_to_prune $PRI_FS \
        | xargs -r zfs list -o $SNAPCOLS
    echo
}


report_source_holds() {
    echo == source holds
    zfs list -t snap -Ho name -s createtxg $PRI_FS \
        | xargs -r zfs holds
    echo

    echo == source holds to release
    get_source_holds_to_release \
        | xargs -r zfs holds \
        | grep -E "^NAME|\s$HOLD_TAG\s" \
        || true
    echo
}


show_count_before() {
    local source_n=$(count_snapshots $PRI_FS)
    local target_n=$(count_snapshots $TARGET_FS)
    local source_p=$(count_prune $PRI_FS)
    local target_p=$(count_prune $TARGET_FS)
    echo == gc $TARGET_ID pre: src=$source_n \
                               dst=$target_n \
                               src_prune=$source_p \
                               dst_prune=$target_p
}


show_count_after() {
    local source_n=$(count_snapshots $PRI_FS)
    local target_n=$(count_snapshots $TARGET_FS)
    echo == gc $TARGET_ID post: src=$source_n dst=$target_n
}


count_prune() {
    local fs=$1
    get_snapshots_to_prune $fs | wc -l
}


count_snapshots() {
    local fs=$1
    zfs list -t snap -d1 -Ho name $fs | wc -l
}


dataset_exists() {
    zfs list -t fs -H $1 &>/dev/null
}


# =======
# testing
# =======


rotate() {
    echo \# zpool export $TARGET_ID-rem
    zpool export $TARGET_ID-rem
    echo
    echo "@@ rotating $TARGET_ID .. $1"
    echo
    TARGET_ID=$1
    TARGET_FS=$TARGET_ID-rem/bak/pri
    HOLD_TAG=pilo:$TARGET_ID-rem
    echo \# zpool import -d /tmp -N $TARGET_ID-rem
    zpool import -d /tmp -N $TARGET_ID-rem
}


postrotate() {
    #_pilo storage-replicate
    show_count_before
    pause
    _pilo storage-stream-replay-all $EXPORT_ROOT/local $TARGET_FS
    #show

    report_gc
    show_count_before
    _pilo storage-stream-gc
    _pilo storage-rotate-gc --preview
    _pilo storage-rotate-gc
    show_count_after
    #show
}

cycle() {
    rotate $1
    postrotate

    for day in 1 2
    do
        for hour in {0..1}
        do
            _pilo storage-snapshot-reg
            _pilo storage-replicate
        done
        _pilo storage-snapshot-mark
        _pilo storage-replicate
        _pilo storage-rollup
    done
}


cleanup() {
    destroy_pool $PRI_POOL $PRI_DEV
    destroy_pool $SEC_POOL1 $SEC_DEV1
    destroy_pool $SEC_POOL2 $SEC_DEV2
    destroy_pool $SEC_POOL3 $SEC_DEV3
    ! [ -d /z ] || find /z -type d -delete
}


test_main() {

    cleanup

    echo \# provisioning

    init_pool $PRI_POOL $PRI_DEV
    _pilo storage-provision-primary
    _pilo storage-init
    _pilo storage-snapshot-mark

    TARGET_ID=z1
    init_pool $SEC_POOL1 $SEC_DEV1
    _pilo storage-provision-secondary z1-rem/bak
    _pilo storage-replica-seed

    TARGET_ID=z2
    zpool export z1-rem
    init_pool $SEC_POOL2 $SEC_DEV2
    _pilo storage-provision-secondary z2-rem/bak
    _pilo storage-replica-seed

    #TARGET_ID=z3
    #zpool export z2-rem
    #init_pool $SEC_POOL3 $SEC_DEV3
    #_pilo storage-provision-secondary z3-rem/bak
    #_pilo storage-replica-seed

    cycle z1
    cycle z2
    cycle z1
    cycle z2
    cycle z1
    cycle z2
    cycle z1
    cycle z2
    #cycle z3
}


show() {
    echo
    echo ====================================================
    zfs list -d1 -t snap,bookmark -o name,userrefs $PRI_FS $TARGET_FS
    zfs list -t snap -d1 -Ho name -s name $PRI_FS $TARGET_FS \
        | xargs zfs holds
    echo ====================================================
    echo
}


pause() {
    echo
    if [ $# -gt 0 ]
    then
        echo "$@"
        echo
    fi
    read -p 'continue/cancel? '
    echo
}




test_main
