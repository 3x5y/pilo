#!/bin/sh
set -e

# break properties
zfs set readonly=off $COLLECTION
#zfs set mountpoint=/wrong $COLLECTION

pilo storage-init

[ "$(zfs get -H -o value readonly $COLLECTION)" = on ] \
    || fail "init did not restore readonly"
#[ "$(zfs get -H -o value mountpoint $PILE)" = "$PILE_PATH" ] \
#    || fail "init did not restore mountpoint"
