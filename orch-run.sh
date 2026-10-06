#!/usr/bin/env bash

set -euo pipefail

PRI_DEV=/tmp/z0
PRI_POOL=z0-att
PRI_FS=z0-att/pri
SEC_DEV1=/tmp/z1
SEC_DEV2=/tmp/z2
SEC_POOL1=z1-rem
SEC_POOL2=z2-rem


_pilo() {
    echo \# pilo "$@" 1>&2
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


catchup() {
    #pause
    #_pilo storage-stream-replay-all $EXPORT_ROOT/local $TARGET_FS
    # TODO: use direct replication here instead
    _pilo storage-replicate
}


gc() {
    _pilo storage-rotate-gc --preview
    _pilo storage-rotate-gc
}


cycle() {
    pause
    rotate $1
    catchup
    gc

    for day in 1 # 2
    do
        for hour in 0 # 1
        do
            _pilo storage-snapshot-reg
            _pilo storage-replicate
        done
        _pilo storage-snapshot-mark
        _pilo storage-replicate
    done
}


cleanup() {
    destroy_pool $PRI_POOL $PRI_DEV
    destroy_pool $SEC_POOL1 $SEC_DEV1
    destroy_pool $SEC_POOL2 $SEC_DEV2
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

    head -c100M /dev/urandom > /z/pile/in/random.bin

    echo \# cycling

    cycle z1
    cycle z2
    cycle z1
    cycle z2
    cycle z1
    cycle z2
    cycle z1
    cycle z2
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
