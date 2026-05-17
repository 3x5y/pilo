#!/bin/sh
set -eu

replica_root=tank/test/replica-alt
alt_replica=$replica_root/alt-data
reset_system tank/test/alt-data
init_replica $replica_root

snap=baseline
pilo snapshot $snap
pilo replica-seed

zfs list -t snapshot | assert_not_grep $TEST_REPLICA@$snap
zfs list -t snapshot | assert_not_grep $TEST_REPLICA/active@$snap
zfs list -t snapshot | assert_grep $alt_replica@$snap
zfs list -t snapshot | assert_grep $alt_replica/active@$snap
