#!/bin/sh
set -eu

python3 - <<EOF
from pilo import zfs

zfs.set_role("$REPLICA_ROOT", zfs.ROLE_REPLICA)

assert zfs.is_replica_root("$REPLICA_ROOT")
assert not zfs.is_primary_root("$REPLICA_ROOT")
EOF
