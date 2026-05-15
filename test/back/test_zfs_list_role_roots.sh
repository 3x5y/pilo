#!/bin/sh
set -eu

python3 - <<EOF
from pilo import zfs

zfs.set_role("$TEST_ROOT", zfs.ROLE_PRIMARY)
zfs.set_role("$REPLICA_ROOT", zfs.ROLE_REPLICA)

roots = zfs.list_role_roots()

assert ("$TEST_ROOT", "primary") in roots
assert ("$REPLICA_ROOT", "replica") in roots
EOF
