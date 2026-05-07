#!/bin/sh
set -eu

col=collection
fil=filing

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
    zpool create -m none -O canmount=off $name "$file"
}

init_primary() {
    local ds=$1
    local mount=$2

    # namespaces
    zfs create -v -o canmount=off -o mountpoint=none $ds
    zfs create -v -o canmount=off -o mountpoint=none $ds/active
    zfs create -v -o canmount=off -o mountpoint=none $ds/static
    zfs create -v -o canmount=off -o mountpoint=$mount/static/filing $ds/static/$fil

    # filesystems
    zfs create -v -o mountpoint=$mount/admin $ds/active/admin
    zfs create -v -o mountpoint=$mount/intake $ds/active/pile-intake
    zfs create -v -o mountpoint=$mount/pile $ds/active/pile-readonly
    zfs create -v -o mountpoint=$mount/static/collection $ds/static/$col
    zfs create -v $ds/static/$fil/2025

    # unused for now
    #zfs create $ds/active/git
    #zfs create $ds/active/special
    #zfs create $ds/active/transient
    #zfs create $ds/active/working
    #zfs create $ds/spool
    #zfs create $ds/stash
}

init_replica() {
    local root=$(dirname $1)
    zfs create -v -o canmount=off -o mountpoint=none $root
}

init_secondary() {
    local root=$1
    local mount=$2

    # namespaces
    zfs create -v -o canmount=off -o mountpoint=$mount $root
    zfs create -v -o canmount=off $root/static
    zfs create -v -o canmount=off $root/static/$fil-annex

    # datasets
    zfs create -v $root/scratch
    zfs create -v $root/static/$col-annex
    #zfs create -v $root/static/$fil-annex/1990-2009
    #zfs create -v $root/static/$fil-annex/2010-2019
}

PRI_DEV=/tmp/z0
SEC_DEV=/tmp/z1

PRI_POOL=z0-att
SEC_POOL=z1-rem

HERE=$(readlink -f $(dirname -- "$0"))
. "$HERE"/pilo.conf.sh

destroy_pool $PRI_POOL $PRI_DEV
destroy_pool $SEC_POOL $SEC_DEV

! [ -d $PILO_PATH ] || find $PILO_PATH -type d -delete

init_pool $PRI_POOL $PRI_DEV
init_pool $SEC_POOL $SEC_DEV

init_primary $PILO_ROOT $PILO_PATH
init_replica $PILO_REPLICA_ROOT $PILO_PATH

# unused for tests
#init_secondary $SEC_POOL/sec $PILO_PATH

