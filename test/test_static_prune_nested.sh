#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

with_writable $PILE mkdir -p /$PILE/out/collection/a/b/c

system-prune-pile

[ ! -d /$PILE/out/collection/a/b/c ] || fail
[ ! -d /$PILE/out/collection/a/b ] || fail
[ ! -d /$PILE/out/collection/a ] || fail
