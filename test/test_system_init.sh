#!/bin/sh
set -e

INTAKE=$TEST_ROOT/active/pile-intake
PILE=$TEST_ROOT/active/pile-readonly
STATIC=$TEST_ROOT/static

system-init

[ $(zfs get -H -o value readonly $INTAKE) = off ] \
    || fail $INTAKE not readonly after init
[ $(zfs get -H -o value readonly $PILE) = on ] \
    || fail $PILE not readonly after init
[ $(zfs get -H -o value readonly $STATIC) = on ] \
    || fail $STATIC not readonly after init
