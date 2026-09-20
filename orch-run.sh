#!/usr/bin/env bash

set -euo pipefail

PRI_DEV=/tmp/z0
PRI_POOL=z0-att
PRI_FS=z0-att/pri
SEC_DEV1=/tmp/z1
SEC_DEV2=/tmp/z2
SEC_POOL1=z1-rem
SEC_POOL2=z2-rem

EXPORT_ROOT=$(mktemp -d)
ln -sfnv $EXPORT_ROOT /tmp/working
mkdir $EXPORT_ROOT/{local,cloud,tmp-export,tmp-import,trash-local,trash-cloud}
chown u:u $EXPORT_ROOT $EXPORT_ROOT/{local,cloud,tmp-export,tmp-import,trash-local,trash-cloud}
export PILO_STREAM_OUTPUT_PATH=$EXPORT_ROOT/local
export PILO_CLOUD_EXPORT_PATH=$EXPORT_ROOT/cloud
export PILO_STREAM_GC_PATH=$EXPORT_ROOT/trash-local
export PILO_CLOUD_GC_PATH=$EXPORT_ROOT/trash-cloud
PILO_AGE_RCPT=age1fptpnrwgum5e67uhjr8uy666mp6fldzwfaagkyvjp8rdpxautp9qpet3a8
PILO_AGE_KEYFILE=/home/u/pilo-enc.key
PILO_MINISIGN_PUBKEY=RWRCmuagslSgwczIVAvxZqdJyLbNb/chzhURhrolpNWBtIESZPOJkFPF
PILO_MINISIGN_KEYFILE=/home/u/pilo-sign.key



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
    pause
    #_pilo storage-stream-replay-all $EXPORT_ROOT/local $TARGET_FS
    # TODO: use direct replication here instead
    _pilo storage-replicate
}


gc() {
    #_pilo storage-stream-gc
    _pilo storage-rotate-gc --preview
    _pilo storage-rotate-gc
    #_pilo storage-stream-gc
    #_pilo storage-stream-gc
    #_pilo storage-stream-gc
    #_pilo storage-cloud-gc \
    #    $EXPORT_ROOT/local \
    #    $EXPORT_ROOT/cloud \
    #    $PILO_MINISIGN_PUBKEY \
    #    --preview
    #_pilo storage-cloud-gc \
    #    $EXPORT_ROOT/local \
    #    $EXPORT_ROOT/cloud \
    #    $PILO_MINISIGN_PUBKEY
}


export_cloud() {
    local stream_dir=$1
    local ymd=$(date +%Y%m%d)
    # TODO: explicit stream-export step here, scoped to the active dataset
    if ls "$stream_dir/$ymd"/*.zfs &>/dev/null
    then
        _pilo storage-stream-verify $stream_dir/$ymd/*.zfs
    fi
    local tmp_dir tar_path
    #tmp_dir=$(mktemp -d)
    tmp_dir=$EXPORT_ROOT/tmp-export
    tar_path=$(_pilo storage-cloud-pack $stream_dir $tmp_dir)
    if [ -z "$tar_path" ]
    then
        echo INFO: nothing to pack, skipping 1>&2
        return
    fi

    local export_root=$PILO_CLOUD_EXPORT_PATH
    _pilo storage-cloud-encrypt \
         --identity $PILO_AGE_KEYFILE \
         $PILO_AGE_RCPT \
         $tar_path \
         $export_root/$ymd

    local tarname=$(basename $tar_path)
    _pilo storage-cloud-sign-manifest \
        $PILO_MINISIGN_KEYFILE \
        $export_root/$ymd/$tarname.age.manifest
}


cycle() {
    rotate $1
    catchup
    gc

    for day in 1 # 2
    do
        for hour in 0 # 1
        do
            _pilo storage-snapshot-reg
            # TODO ensure replicate is not doing exports
            _pilo storage-replicate
            #export_cloud $EXPORT_ROOT/local
        done
        _pilo storage-snapshot-mark
        # TODO ensure replicate is not doing exports
        _pilo storage-replicate
        #_pilo storage-rollup
        #export_cloud $EXPORT_ROOT/local
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

    #export_cloud $EXPORT_ROOT/local

    TARGET_ID=z1
    init_pool $SEC_POOL1 $SEC_DEV1
    _pilo storage-provision-secondary z1-rem/bak
    _pilo storage-replica-seed

    TARGET_ID=z2
    zpool export z1-rem
    init_pool $SEC_POOL2 $SEC_DEV2
    _pilo storage-provision-secondary z2-rem/bak
    _pilo storage-replica-seed

    head -c100M /dev/urandom > /z/intake/random.bin

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
