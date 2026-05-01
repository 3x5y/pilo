#!/bin/sh
set -e

alt_root=tank/alt-data
alt_replica_root=tank/replica-alt
alt_replica=tank/replica-alt/alt-data
init_system $alt_root /$alt_root $alt_replica_root

snap=baseline
system-snapshot $snap
system-replicate

zfs list -t snapshot | assert_not_grep $TEST_REPLICA@$snap
zfs list -t snapshot | assert_not_grep $TEST_REPLICA/active@$snap
zfs list -t snapshot | assert_grep $alt_replica@$snap
zfs list -t snapshot | assert_grep $alt_replica/active@$snap
