#!/bin/sh
set -e

alt_root=tank/alt-data
alt_replica_root=tank/replica-alt
alt_replica=tank/replica-alt/alt-data
zfs destroy -r $alt_root 2>/dev/null || true
zfs destroy -r $alt_replica 2>/dev/null || true
zfs create $alt_root
zfs create $alt_replica_root
init_datasets $alt_root

export SYSTEM_ROOT=$alt_root
export SYSTEM_PATH=/$alt_root
export SYSTEM_REPLICA_ROOT=$alt_replica
system-init

snap=baseline
system-snapshot $snap
system-replicate

zfs list -t snapshot | assert_not_grep $TEST_REPLICA@$snap
zfs list -t snapshot | assert_not_grep $TEST_REPLICA/active@$snap
zfs list -t snapshot | assert_grep $alt_replica@$snap
zfs list -t snapshot | assert_grep $alt_replica/active@$snap
