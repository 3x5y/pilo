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
    zpool create -m none -O canmount=off -O mountpoint=none $name "$file"
}

init_primary() {
    local ds=$1
    local mount=$2
    local user=$3

    # namespaces
    zfs create -o canmount=off -o mountpoint=$mount $ds
    zfs create -o canmount=off -o mountpoint=$mount $ds/active
    zfs create -o canmount=off $ds/static
    zfs create -o canmount=off $ds/static/$fil

    # datasets
    zfs create $ds/active/pile-readonly
    zfs create $ds/active/pile-intake
    zfs create $ds/active/admin
    zfs create $ds/static/$col
    zfs create $ds/static/$fil/2025

    # unused for tests
    #zfs create $ds/active/git
    #zfs create $ds/active/special
    #zfs create $ds/active/transient
    #zfs create $ds/active/working
    #zfs create $ds/spool
    #zfs create $ds/stash

    chown $user:$user $mount/pile-intake
    chown $user:$user $mount/pile-readonly
    chown $user:$user $mount/admin
    chown $user:$user $mount/static/$col
    chown $user:$user $mount/static/$fil/2025

    # unused for tests
    #chown $user:$user $mount/git
    #chown $user:$user $mount/special
    #chown $user:$user $mount/spool
    #chown $user:$user $mount/stash
    #chown $user:$user $mount/transient
    #chown $user:$user $mount/working

    # defer to `pilo init`
    #zfs set readonly=on $ds/active/pile-readonly
    #zfs set readonly=on $ds/static/$col
    #zfs set readonly=on $ds/static/$fil/2025
}

init_replica() {
    local root=$1
    zfs create -o canmount=off -o mountpoint=none $root
}

init_secondary() {
    local root=$1
    local mount=$2
    local user=$3

    # namespaces
    zfs create -o canmount=off -o mountpoint=$mount $root
    zfs create -o canmount=off $root/static
    zfs create -o canmount=off $root/static/$fil-annex

    # datasets
    zfs create $root/scratch
    zfs create $root/static/$col-annex
    zfs create $root/static/$fil-annex/1990-2009
    zfs create $root/static/$fil-annex/2010-2019

    chown $user:$user $mount/scratch
    chown $user:$user $mount/static/$col-annex
    chown $user:$user $mount/static/$fil-annex/1990-2009
    chown $user:$user $mount/static/$fil-annex/2010-2019

    zfs set readonly=on $root/static/$col-annex
    zfs set readonly=on $root/static/$fil-annex/1990-2009
    zfs set readonly=on $root/static/$fil-annex/2010-2019
}

PRI_POOL=z0-att
PRI_DEV=/tmp/z0

SEC_POOL=z1-rem
SEC_DEV=/tmp/z1

destroy_pool $PRI_POOL $PRI_DEV
destroy_pool $SEC_POOL $SEC_DEV
find /z -type d -delete

init_pool $PRI_POOL $PRI_DEV
init_pool $SEC_POOL $SEC_DEV

init_primary $PRI_POOL/pri /z user
init_replica $SEC_POOL/bak /z user
# unused for tests
#init_secondary $SEC_POOL/sec /z user

