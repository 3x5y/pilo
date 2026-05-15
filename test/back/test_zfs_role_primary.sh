#!/bin/sh
set -eu

python3 - <<EOF
from pilo import zfs

zfs.set_role("$TEST_ROOT", zfs.ROLE_PRIMARY)

assert zfs.is_primary_root("$TEST_ROOT")
assert not zfs.is_replica_root("$TEST_ROOT")
EOF
