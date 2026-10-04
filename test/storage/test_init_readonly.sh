#!/bin/sh
set -e

[ $(zfs get -H -o value readonly $INTAKE) = off ] \
    || fail $INTAKE readonly after init
[ "$(zfs get -H -o value canmount $INTAKE)" = on ] \
    || fail "intake canmount incorrect"
#[ $(zfs get -H -o value readonly $PILE) = on ] \
#    || fail $PILE not readonly after init
[ "$(zfs get -H -o value canmount $PILE)" = on ] \
    || fail "$PILE canmount incorrect"
[ $(zfs get -H -o value readonly $COLLECTION) = on ] \
    || fail $COLLECTION not readonly after init
[ "$(zfs get -H -o value canmount $COLLECTION)" = on ] \
    || fail "$COLLECTION canmount incorrect"
