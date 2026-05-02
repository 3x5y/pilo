#!/bin/sh
set -e

export PILO_ADMIN_PATH=$TMP/pilo-admin
zfs set mountpoint=$PILO_ADMIN_PATH $ADMIN
pilo init

[ -d "$PILO_ADMIN_PATH" ] || fail "override path not respected"
