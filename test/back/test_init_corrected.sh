#!/bin/sh
set -e

# break properties
zfs set readonly=off $PILE
#zfs set mountpoint=/wrong $PILE

pilo init

[ "$(zfs get -H -o value readonly $PILE)" = on ] \
    || fail "init did not restore readonly"
#[ "$(zfs get -H -o value mountpoint $PILE)" = "$PILE_PATH" ] \
#    || fail "init did not restore mountpoint"
