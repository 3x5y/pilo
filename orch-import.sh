#!/bin/bash

set -eu
set -o pipefail


PILO_AGE_KEYFILE=$HOME/pilo-enc.key
PILO_MINISIGN_PUBKEY=RWRCmuagslSgwczIVAvxZqdJyLbNb/chzhURhrolpNWBtIESZPOJkFPF


import_file() {
    local age_file=$1
    local import_root=$WORKING_ROOT/import
    local tmp_dir=$WORKING_ROOT/tmp-import
    pilo storage-cloud-verify-manifest \
        $PILO_MINISIGN_PUBKEY $age_file.manifest

    local tar_file=$(pilo storage-cloud-decrypt $PILO_AGE_KEYFILE $age_file $tmp_dir)
    pilo storage-cloud-unpack $tar_file $import_root $age_file.manifest
    stamp=$(basename $age_file .tar.zst.age)
    pilo storage-stream-verify $import_root/$stamp/*/*.zfs
}


WORKING_ROOT=$1

for dir in $WORKING_ROOT/cloud/*
do
    for age_file in $dir/*.age
    do
        import_file $age_file
    done
done

