#!/bin/sh
set -e

COLL=$STATIC/collection

[ $(zfs get -H -o value readonly $INTAKE) = off ] \
    || fail $INTAKE not readonly after init
[ "$(zfs get -H -o value canmount $INTAKE)" = on ] \
    || fail "intake canmount incorrect"
[ $(zfs get -H -o value readonly $PILE) = on ] \
    || fail $PILE not readonly after init
[ "$(zfs get -H -o value canmount $PILE)" = on ] \
    || fail "intake canmount incorrect"
[ $(zfs get -H -o value readonly $COLL) = on ] \
    || fail $COLL not readonly after init
[ "$(zfs get -H -o value canmount $PILE)" = on ] \
    || fail "intake canmount incorrect"
